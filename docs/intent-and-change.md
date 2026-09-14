# Project Frame

## Reservation domain
Rezervace sportovišť

## Purpose
Systém slouží zákazníkům ke snadné rezervaci sportovišť na konkrétní datum a čas. Provozovatelům umožňuje spravovat dostupnost sportovišť a potvrzovat nebo rušit rezervace.

## Users / Stakeholders
Zákazník – vytváří a ruší rezervace.
Správce sportoviště – schvaluje rezervace a spravuje sportoviště.
Provozovatel – sleduje využití a dostupnost sportovišť.

## Core concepts
Reservation – rezervace sportoviště na určitý čas.
Resource – sportoviště, které lze rezervovat.
User – osoba, která rezervaci vytváří.
Sport – typ sportovní aktivity, pro kterou je sportoviště určeno.

## Core operations
- Create reservation
- Confirm / approve reservation
- Cancel reservation
- Check availability

## Persistent state

Reservation:
ID rezervace
User
Resource
Datum a čas začátku
Datum a čas konce
Stav rezervace
Datum vytvoření

Resource:
ID sportoviště
Název
Typ sportoviště
Lokalita
Otevírací doba
Aktuální stav dostupnosti

## State-changing operation
DRAFT → CONFIRMED → CANCELLED
Po vytvoření je rezervace ve stavu DRAFT. Po schválení správcem přejde do CONFIRMED; následně ji lze zrušit a přejde do CANCELLED.

## Common business rule
Dvě potvrzené rezervace stejného sportoviště se nesmí časově překrývat.

## Domain-specific business rule
Rezervaci sportoviště lze vytvořit maximálně 30 dní dopředu a maximální délka jedné rezervace je 2 hodiny.

## External / system boundary
Notification Service – systém jej používá pro odesílání potvrzení rezervace, změn a upozornění na zrušení rezervace.

## Assumption
Předpokládáme, že každé sportoviště má jednu pevně definovanou dostupnost podle své otevírací doby.

## Unknown
Není zatím jasné, zda musí být každá rezervace schválena správcem, nebo zda se má po vytvoření automaticky potvrdit.
