# Lösung T3/03

```bash
uv sync
uv run python guardrail.py   # eigener Guardrail (Medizin-Thema statt Anlageberatung)
uv run pytest -v             # 3 Tests: verbotenes Thema + Injection-Dokument abgewehrt
uv run python cleanup.py     # Guardrail löschen
```

Der Kern der Übung ist die **Abwehr indirekter Prompt-Injection** — nicht die Frage des Nutzers, sondern ein vergiftetes Dokument in der Wissensbasis:

- [safe_ingest.py](safe_ingest.py): Jedes Dokument wird per `apply_guardrail` (`source="INPUT"`) geprüft, **bevor** es in den Store kommt. Ein converse-Guardrail käme zu spät — er sieht das Dokument erst, wenn das Retrieval es schon in den Prompt gelegt hat. Der Schutz gehört an den **Ingest**, nicht an die Anfrage.
- [guardrail.py](guardrail.py): eigenes verbotenes Thema (Medizinische Beratung), damit ihr die Policy **entwerft** statt sie zu kopieren. `PROMPT_ATTACK`-Filter fängt die Injection-Nutzlast im Dokument — live verifiziert: der Angriffstext triggert, ein sauberer Reisebericht nicht.

Stolpersteine:

- **`PROMPT_ATTACK` nur mit `inputStrength`** — `outputStrength` muss `NONE` sein, sonst `ValidationException` beim Anlegen.
- **`apply_guardrail` vs. `converse`-Guardrail**: Der erste prüft beliebigen Text ohne Modell-Call (unser Ingest-Scan), der zweite hängt am Antwort-Call. Für indirekte Injection braucht ihr den ersten.
- **Kein CDK-L2**: Guardrail per boto3 angelegt; in Produktion `CfnGuardrail` (L1) in der CDK-App.
- **False Positives im Blick behalten**: Ein zu aggressiver `PROMPT_ATTACK`-Filter würde legitime Dokumente ablehnen — der dritte Test (`test_clean_documents_are_not_falsely_rejected`) ist genau dafür da.
