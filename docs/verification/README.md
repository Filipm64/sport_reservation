# Ověřování a vazby

[Přehled dokumentace](../README.md)

- [Aktuální týdenní tabulka a provozní doba — REQ-12/13](weekly-operating-hours.md)
- [REQ-12: hodinový rozvrh, limit 2 hodin a ověření UI](hourly-schedule.md)
- [REQ-07 až REQ-11: ověření portálu a vztah k zadáním](portal-requirements.md)
- [Aktuální životní cyklus, migrace a ověření](reservation-lifecycle.md)
- [Požadavky → návrh → implementace → testy](coverage.md)
- [Zpětné vazby z metod a testů na požadavky](coverage.md#zpětné-vazby-z-kódu-a-testů)
- [Aktuální změna expirace čekajících žádostí](approval-expiration.md)
- [Ověření chování — L1](behavior.md)
- [Ověření architektonického pravidla — L2](architecture-rules.md)
- [Kontrola konzistence pohledů — I](cross-view-check.md)
- [Výstup ověření C03](evidence/c03-final-verification.log)
- [Výstup architektonického testu L2](evidence/l2-architecture-test.log)
- [Historická evidence a vývoj](../history/evidence-and-evolution.md)

## Údržba vazeb

[traceability.json](traceability.json) je jediný registr vazeb. Každý záznam má stabilní ID, stránku požadavku, ID pravidel, návrhové dokumenty a seznamy symbolů implementace a testů. Cesty jsou od kořene repozitáře; symbol je například `ReservationApiTests.test_delayed_approval_succeeds_before_timeout`.

Z kořene repozitáře:

```sh
python3 scripts/update_docs.py
python3 scripts/update_docs.py --check
```

[Skript](../../scripts/update_docs.py) generuje oba směry přehledu, vyhledává symboly přes Python AST a kontroluje lokální Markdown odkazy. Neprovádí testy aplikace ani neposuzuje věcnou správnost vazeb. Postup spuštění aplikačních testů je v [README projektu](../../README.md#reprodukovatelné-ověření).
