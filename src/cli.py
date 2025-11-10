"""Command line interface for interacting with the guardrail pipeline."""

# docker run -it pii-guardrails:latest --rules-path /app/rules_nl.yaml

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .logging_util import setup_logging
from .pipeline import GuardrailPipeline, PipelineResult

app = typer.Typer(help="Professionele CLI voor het evalueren van prompts met guardrails.")

console = Console()


class CLIState:
    """Houdt gedeelde status tussen commando's bij."""

    def __init__(self, rules_path: Path, log_level: str) -> None:
        self.rules_path = rules_path
        self.log_level = log_level
        self.pipeline: Optional[GuardrailPipeline] = None

    def load_pipeline(self) -> None:
        self.pipeline = GuardrailPipeline.from_yaml(self.rules_path)


def _render_result(result: PipelineResult) -> None:
    if not result.is_blocked:
        console.print(
            Panel.fit(
                "Prompt is toegestaan", title="OK", border_style="green", highlight=True
            )
        )
        return

    table = Table(
        title="Geblokkeerde prompt",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold red",
    )
    table.add_column("Regel ID", style="cyan", no_wrap=True)
    table.add_column("Categorie", style="magenta")
    table.add_column("Ernst", style="yellow")
    table.add_column("Match", style="white")
    table.add_column("Toelichting", style="white")

    for match in result.matches:
        table.add_row(
            match.rule_id,
            match.category,
            match.severity.capitalize(),
            match.match_text,
            match.explanation,
        )

    highest_severity = result.highest_severity()
    console.print(
        Panel(
            table,
            title="BLOCKED",
            border_style="red",
            subtitle=f"Hoogste ernst: {highest_severity}" if highest_severity else "",
        )
    )


def _show_help() -> None:
    help_table = Table(title="Beschikbare commando's", box=box.SIMPLE_HEAVY)
    help_table.add_column("Commando", style="cyan", justify="left")
    help_table.add_column("Omschrijving", style="white")
    help_table.add_row(":help", "Toon dit help scherm")
    help_table.add_row(":reload", "Herlaad de regels van het opgegeven YAML-bestand")
    help_table.add_row(":rules", "Toon het pad naar het huidige regels-bestand")
    help_table.add_row(":export", "Exporteer de laatste evaluatie als JSON bestand")
    help_table.add_row(":quit", "Verlaat de applicatie")
    console.print(help_table)


def _export_result(result: Optional[PipelineResult], export_path: Path) -> None:
    if result is None:
        console.print("[yellow]Geen resultaat beschikbaar om te exporteren.[/yellow]")
        return

    payload = {
        "prompt": result.prompt,
        "status": result.status,
        "matches": [
            {
                "rule_id": match.rule_id,
                "category": match.category,
                "severity": match.severity,
                "match_text": match.match_text,
                "start": match.start,
                "end": match.end,
                "explanation": match.explanation,
            }
            for match in result.matches
        ],
    }

    export_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"[green]Resultaat opgeslagen naar {export_path}[/green]")


def _create_session(history_file: Optional[Path]) -> PromptSession:
    completer = WordCompleter(":help :quit :reload :rules :export".split(), ignore_case=True)
    history = FileHistory(str(history_file)) if history_file else None
    return PromptSession(completer=completer, history=history)


@app.command()
def run(
    rules_path: Path = typer.Option(
        Path("rules_nl.yaml"),
        "--rules-path",
        "-r",
        help="Pad naar het YAML-bestand met guardrail regels.",
    ),
    log_level: str = typer.Option("INFO", help="Logging niveau (bijv. INFO of DEBUG)."),
    history_file: Optional[Path] = typer.Option(
        None,
        "--history-file",
        help="Optioneel bestand om prompt geschiedenis in op te slaan.",
    ),
) -> None:
    """Start de interactieve prompt interface."""

    setup_logging(level=log_level)
    state = CLIState(rules_path=rules_path, log_level=log_level)

    try:
        state.load_pipeline()
    except FileNotFoundError:
        console.print(f"[red]Regelbestand niet gevonden: {rules_path}[/red]")
        raise typer.Exit(code=1) from None
    except Exception as exc:  # pragma: no cover - defensieve foutmelding
        logging.exception("Kon regels niet laden")
        console.print(f"[red]Kon regels niet laden: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(Panel.fit("Guardrail CLI gestart. Typ :help voor opties.", border_style="blue"))

    session = _create_session(history_file)
    last_result: Optional[PipelineResult] = None

    while True:
        try:
            user_input = session.prompt("prompt> ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]Tot ziens![/cyan]")
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        if stripped.startswith(":"):
            command_raw = stripped[1:]
            command = command_raw.lower()
            if command in {"quit", "exit"}:
                console.print("[cyan]Tot ziens![/cyan]")
                break
            if command == "help":
                _show_help()
                continue
            if command == "reload":
                try:
                    state.load_pipeline()
                    console.print("[green]Regels opnieuw geladen.[/green]")
                except Exception as exc:  # pragma: no cover - defensieve foutmelding
                    logging.exception("Fout bij herladen van regels")
                    console.print(f"[red]Fout bij herladen: {exc}[/red]")
                continue
            if command == "rules":
                console.print(f"Huidig regels-bestand: {state.rules_path}")
                continue
            if command.startswith("export"):
                parts = command_raw.split(maxsplit=1)
                if len(parts) == 2:
                    export_path = Path(parts[1]).expanduser()
                else:
                    export_path = Path("guardrail-resultaat.json")
                _export_result(last_result, export_path)
                continue

            console.print(f"[yellow]Onbekend commando: {command}[/yellow]")
            continue

        assert state.pipeline is not None
        last_result = state.pipeline.evaluate(stripped)
        _render_result(last_result)


def main() -> None:
    """CLI entrypoint voor console scripts."""

    app()


if __name__ == "__main__":
    main()