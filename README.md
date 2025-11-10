# PII-Guardrails-PoC

Een **Proof-of-Concept** voor **PII-detectie met Regex Guardrails**.  
Doel: op een transparante, reproduceerbare manier PII-patronen (zoals NL-telefoonnummers, e-mailadressen, IBAN, postcode, etc.) detecteren in **prompts** (input) zonder afhankelijk te zijn van externe diensten.

> **TL;DR**  
> - Start lokaal: `python -m src.cli --rules-path rules_nl.yaml`  
> - Start met Docker: `docker run -it pii-guardrails:latest --rules-path /app/rules_nl.yaml`  
> - Regels kunnen geschreven worden in `rules_nl.yaml` met **regex** per PII-type.

---

## Achtergrond
Deze PoC is gebouwd om **eenvoudige, verklaarbare guardrails** te testen voor PII-detectie in een LLM-context.  
In plaats van zware frameworks gebruikt dit project **pure regex-regels** die zelf beheerbaar zijn.  
Dit maakt gedrag **voorspelbaar**, **snel** en **auditeerbaar**.

---

## Snel starten
```bash
# (A) Lokaal
python -m src.cli --rules-path rules_nl.yaml

# (B) Docker (image moet al gebouwd zijn)
docker run -it pii-guardrails:latest --rules-path /app/rules_nl.yaml

```

## Installatie (lokaal)

### 1. Vereisten
- Python 3.10+ (aanbevolen 3.11)
- pip en venv

### 2. Repository klonen
Voer de standaard Git-commando’s uit om de repo te klonen.

### 3. Virtuele omgeving & dependencies installeren
Maak een virtuele omgeving aan en installeer de vereiste pakketten met `pip install -r requirements.txt`.

### 4. CLI uitvoeren
Activeer de virtuele omgeving en start de CLI met:
`python -m src.cli --rules-path rules_nl.yaml`

---

## Gebruik

Wanneer je de CLI start, opent een interactieve prompt waarin je tekst kunt invoeren.  
De tool scant vervolgens de invoer op PII en geeft één van de volgende resultaten:

- **PASS** – geen PII gedetecteerd  
- **FAIL** – één of meerdere regels zijn gematcht  

De CLI ondersteunt argumenten zoals:
- `--rules-path PATH` → pad naar de YAML-regels (verplicht)  
- `--log-level LEVEL` → optioneel logniveau (bijv. `INFO`, `DEBUG`)

---

## Regelbestanden (YAML)

De regex-regels staan in een YAML-bestand, standaard `rules_nl.yaml`.  
Elke regel bevat minimaal een ID, beschrijving en regex-patroon.  
Optioneel kunnen ook voorbeelddata worden toegevoegd.

**Voorbeeld:**
```yaml
rules:
  - id: nl_mobile_phone
    description: "Nederlands mobiel nummer (+31/0031/0 6-xxxxxxxx)"
    pattern: "(?:\\+31|0031|0)\\s?6[\\s-]?\\d{8}"

  - id: email
    description: "E-mailadres"
    pattern: "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"
