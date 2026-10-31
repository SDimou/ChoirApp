# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

ChoirApp — single-tenant Streamlit app for managing a choir (χορωδία): members, voice
sections, repertoire (musical pieces + composers/lyricists), and events (rehearsals/concerts)
with attendance tracking. Greek-language UI and domain naming throughout — table/column
names, function names, and view labels are Greek transliterations (e.g. `Xorodoi` = χορωδοί
= choir members, `Kommatia` = κομμάτια = pieces, `Ekdiloseis` = εκδηλώσεις = events). Keep
this convention when adding code — don't translate existing identifiers to English.

## Commands

Run the app:
```
streamlit run ChoirApp.py
```
(or double-click `ChoirApp.bat`, which cds to the deployed path and launches streamlit)

Install dependencies:
```
pip install -r requirements.txt
```

Apply/reset the DB schema (drops and recreates all tables, then reseeds `Foni`):
```
sqlcmd -S <server> -i db\schema.sql
```

Grant a Windows account access to the DB (edit the login name in the file first):
```
sqlcmd -S <server> -i db\grant_access.sql
```

No test suite, linter, or build step currently exists in this repo.

## Architecture

**Streamlit multipage app**, entry point [ChoirApp.py](ChoirApp.py), which declares
navigation via `st.navigation` over pages in [views/](views/):
- [views/xorodoi.py](views/xorodoi.py) — choir members (Atomo) + their voice section (Foni)
- [views/kommatia.py](views/kommatia.py) — repertoire pieces (Kommati), linked many-to-many
  to composers (Synthetis) and lyricists (Stixourgos)
- [views/ekdiloseis.py](views/ekdiloseis.py) — rehearsals/concerts (Ekdilosi), attendance
  (SymmetoxesEkdilosis), and per-event repertoire (KommatiaEkdilosis)
- [views/anafora_data.py](views/anafora_data.py) — reference data CRUD: voice sections,
  composers, lyricists
- [views/sbismena.py](views/sbismena.py) — soft-deleted events, members and pieces, with restore

**Data layer**: [database.py](database.py) is the sole DB access point — every view imports
functions from it, none run SQL directly. All queries go through raw parameterized SQL via
SQLAlchemy's `text()`, not an ORM (no models). `read_df()` returns a pandas DataFrame,
`execute()` runs a write in an auto-committing transaction. Multi-statement writes open their
own `get_engine().begin()` block for atomicity (see `add_kommati`, `delete_ekdilosi`, etc.).
When adding a DB function, follow this pattern rather than introducing a new access style.

**Connection**: SQL Server via `pyodbc`/`mssql+pyodbc`, Windows Trusted Connection (no
password auth). The server instance is resolved by machine hostname
(`platform.node()`) against the `KNOWN_SERVERS` map in [database.py](database.py:12), or
overridden with the `CHOIRAPP_DB_SERVER` env var. Add new deployment machines to that map.
Each Windows account that needs access must additionally be granted a DB user via
[db/grant_access.sql](db/grant_access.sql) (login existing in SQL Server isn't sufficient).

**Schema** ([db/schema.sql](db/schema.sql)) — key design decisions (documented in the SQL
file's header, in Greek):
1. `Ekdilosi` is a shared base table for both rehearsals and concerts
   (`EventType`: `'P'`=Πρόβα/rehearsal, `'S'`=Συναυλία/concert), with `Prova` and `Synavlia`
   as subtype tables holding type-specific fields. A composite FK on `(EkdilosiID, EventType)`
   enforces that a `Synavlia` row can never point at a `'P'` `Ekdilosi` row (and vice versa),
   without triggers.
2. `Kommati` (piece) → `Synthetis`/`Stixourgos` (composer/lyricist) are many-to-many via
   junction tables `KommatiaSynthetes`/`KommatiaStixourgoi`, since a piece can have multiple
   composers or lyricists.
3. `SymmetoxesEkdilosis` (attendance) and `KommatiaEkdilosis` (per-event repertoire) are
   unified junction tables keyed on `Ekdilosi`, so rehearsals and concerts share one pair of
   link tables instead of needing separate ones per event type.

Soft delete: `Ekdilosi`, `Atomo` and `Kommati` have an `IsDeleted` bit. `delete_atomo`,
`delete_kommati` and `delete_ekdilosi` only set it to 1, never `DELETE`, so junction rows stay
intact and come back on restore from [views/sbismena.py](views/sbismena.py). Every query on
these tables must filter `IsDeleted = 0`, including joins through the junction tables. All
other deletes are permanent, and soft-deleted rows still block lookup deletes (`Foni`,
`Synthetis`, `Stixourgos`) via FK.

## UI patterns used across views

- Editable grids: `st.data_editor(..., num_rows="dynamic")` for list CRUD (members, voice
  sections), diffed against original IDs on save to compute inserts/updates/deletes — see
  [views/xorodoi.py](views/xorodoi.py) and the `Foni` tab in
  [views/anafora_data.py](views/anafora_data.py).
- Form CRUD via `st.selectbox` + fields for single-entity add/edit (pieces) — see
  [views/kommatia.py](views/kommatia.py).
- `st.dialog` modals for multi-step create/detail flows (new event, event detail with tabs
  for attendance and repertoire) — see [views/ekdiloseis.py](views/ekdiloseis.py).
- Every delete button asks for confirmation: `confirm_delete_dialog` in [utils.py](utils.py),
  or `st.popover` when already inside a dialog (Streamlit has no nested dialogs).
- Deletes that violate FK constraints (e.g. deleting a `Foni`/`Synthetis`/`Stixourgos` still
  in use) are caught as `sqlalchemy.exc.IntegrityError` and surfaced as an `st.error`, not
  prevented up front — follow this pattern rather than pre-checking references.
