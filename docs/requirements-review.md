# Revize a dohledatelnost požadavků C02

Technická revize 5. 10. 2026. ID níže označují pozorovatelné požadavky
v operacích obou baseline, nepřepisují doménová pravidla.
Nejde o náhradu skutečného týmového přijetí.

| ID / operace | Význam, potřeba a pozorovatelný výsledek | Ověření splnění / porušení | Stav, čas, souběh a konzistence | Nejistota / zdroj |
| --- | --- | --- | --- | --- |
| REQ-01 / OP-01 | Přihlášený zákazník zaznamená záměr: právě jedna DRAFT pro existující Resource a platný interval. Create nealokuje ani neodmítá kvůli kolizi. | `test_create_succeeds_and_rejects_invalid_interval`, `test_exact_time_limits_and_exceeded_limits`, `test_authentication_ownership_and_unknown_resource`, `test_invalid_calendar_date_returns_error_without_creating`. Neplatný vstup nesmí nic vytvořit. | BR-01/03; dva Create mohou vytvořit dvě DRAFT, invariant není porušen. Beze změny v0.2; souhlasí s diagramy. | Zadání C02 a původní projektový rámec; business důvod limitů má potvrdit tým. |
| REQ-02 / OP-02 | Přihlášený zákazník zjistí momentální dostupnost bez změny stavu. Blokuje pouze CONFIRMED a nedostupný Resource; výsledek není garance následného Confirm. | `test_availability_checks_confirmed_only_and_half_open_edges`, `test_approval_request_does_not_block_until_staff_approves`, `test_inactive_resource_and_invalid_availability`. Sousední interval AVAILABLE, překryv UNAVAILABLE, neplatný interval chyba. | BR-01 až BR-04; současné Confirm může změnit další výsledek dotazu. PENDING_APPROVAL neblokuje; v0.2 zachováno. | C02; neblokování čekajících žádostí je explicitní volba k potvrzení týmem. |
| REQ-03 / OP-03 | Jen vlastník DRAFT požádá o potvrzení; platný čas, aktivní Resource a žádná kolize. V0.1 CONFIRMED, ve v0.2 podle příznaku také PENDING_APPROVAL. | `test_confirm_conflict_is_rejected_and_normal_confirm_succeeds`, `test_inactive_resource_and_invalid_availability`, `test_approval_request_does_not_block_until_staff_approves`. Neúspěch ponechá DRAFT. | BR-01 až BR-04/07; kolize se ověří při změně, nikoliv jen při předchozím dotazu. Souhlasí s větvením diagramu. | C02 změna; oprávnění vlastníka a příznak Resource jsou stávající politika. |
| REQ-04 / OP-03 a OP-05 | Nikdy dvě kolidující CONFIRMED stejného Resource. Jde o business výsledek, ne předepsanou databázi. | `test_conflicting_confirmations_commit_only_one_allocation`, `test_conflicting_approvals_commit_only_one_allocation`, `test_confirm_racing_approval_commits_only_one_allocation`: jedna 200, druhá 409 a jen jedna CONFIRMED. | BR-02/06; souběh nad různými rezervacemi stejného Resource. Availability je pouze informativní. | C02 výslovně požaduje souběh; provozní zatížení a budoucí DB jsou TBD pro C03. |
| REQ-05 / OP-04 | Vlastník před začátkem zruší DRAFT/CONFIRMED, ve v0.2 také platnou PENDING_APPROVAL. CANCELLED neblokuje a záznam zůstane. | `test_cancel_draft_and_confirmed_releases_resource_and_rejects_repeat`, `test_owner_can_cancel_pending_approval_but_not_after_start`, `test_cancel_at_exact_start_is_rejected`, dva testy závodu Cancel v `ReservationConcurrencyTests`. | BR-05/06/07; `now < start`, po expiraci EXPIRED. Confirm/Approve první může následovat úspěšný Cancel; Cancel první znemožní Confirm/Approve. | C02 vyžaduje vlastní politiku rušení; převzatou politiku musí tým potvrdit. |
| REQ-06 / OP-05 (jen v0.2) | Přihlášený správce rozhodne o platné PENDING_APPROVAL. Schválení znovu ověří alokaci, zamítnutí REJECTED, při deadline EXPIRED a odmítnuto. | `test_delayed_approval_succeeds_before_timeout`, `test_staff_can_reject_but_non_staff_cannot_decide`, `test_new_conflict_prevents_approval_and_leaves_request_pending`, `test_expiry_exact_deadline_on_approve_cancel_and_command`. | BR-01 až BR-04/06/07; nejdřívější z 24 h a start, serverový čas. Expirace má přednost před rozhodnutím i zrušením. Diagram obsahuje všechny čtyři výsledky PENDING_APPROVAL. | C02 změna; 24 h a `is_staff` jsou existující volby, doklad souhlasu chybí. |

## Společné závěry revize

- **Proveditelnost:** požadavky se navzájem nevylučují. Create může uspět
  i na obsazený Resource, protože DRAFT nealokuje. Availability i
  Confirm/Approve používají stejnou definici kolize.
- **Pozorovatelnost:** názvy Django, SQLite a IMMEDIATE patří do evidence
  a driverů, nikoli do požadavku na business výsledek.
- **Konzistence:** opraven nesprávný SVG přechod CONFIRMED → REJECTED
  označený Cancel a neukončená hrana DRAFT → CANCELLED. Opraveno tvrzení,
  že při závodu Approve/Cancel musí vždy uspět jen jedna operace.
- **Nejistota:** týmové přijetí pravidel a historické odsouhlasení v0.1
  není doloženo. Rozhodnutí nesmí být prezentováno jako schválené jen
  proto, že kód a automatické testy souhlasí.
