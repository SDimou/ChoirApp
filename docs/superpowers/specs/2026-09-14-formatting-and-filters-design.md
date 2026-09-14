# Formatting & filters — design

Date: 2026-09-14

## Purpose

Four UX changes to the ChoirApp Streamlit app:

1. All dates shown to the user render as `dd/mm/yy`, regardless of underlying storage.
2. All full-name display/input shows "Όνομα Επώνυμο" (name first, surname second) —
   including table columns, not just concatenated labels.
3. "Χορωδοί" page: default sort is by voice section (Foni) in a specific order
   (Soprano, Baladeur, Alto), then alphabetically (by surname) within each section.
   Add a voice-section filter dropdown.
4. "Πρόβες & Συναυλίες" page: add an event-type filter (Όλα/Πρόβες/Συναυλίες) and a
   month/year filter.

## Out of scope

- Xronia (composition year) on Kommati is a bare year integer, not a date — not touched.
- No change to sort keys used for underlying queries, only to what's displayed.

## 1. Date format (dd/mm/yy)

New module `utils.py` (root, alongside `database.py`) holds cross-page display helpers:

```python
def format_date(d):
    """Return d as 'dd/mm/yy', or '' if d is None/NaT."""
```

Applied everywhere a date is shown to the user:
- [views/ekdiloseis.py](../../../views/ekdiloseis.py): event list row date, and the
  view-dialog subheader date — both currently `strftime('%d/%m/%Y')`, switch to
  `format_date()`.

Applied to date input:
- `st.date_input("Ημερομηνία")` in the new-event dialog gets `format="DD/MM/YYYY"`.

**Constraint discovered during research**: `st.date_input`'s `format` parameter only
accepts 4-digit-year variants (`"YYYY/MM/DD"`, `"DD/MM/YYYY"`, `"MM/DD/YYYY"`) — there is
no 2-digit-year option for the calendar widget itself. So the *input* widget will show
`DD/MM/YYYY` (correct day-month-year order, 4-digit year); the `dd/mm/yy` requirement is
met everywhere dates are *displayed* (list rows, dialog headers), which is achievable
exactly.

## 2. Name-first display ("Όνομα Επώνυμο"), everywhere including table columns

New helper in `utils.py`:

```python
def person_label(onoma, eponymo):
    """Return 'Onoma Eponymo', trimmed, for display."""
```

Scope confirmed with user: applies to *every* place a full name is shown, including
`st.data_editor`/`st.dataframe` tables with separate Onoma/Eponymo columns — column order
swaps to Onoma-first there too.

Changes:
- [database.py](../../../database.py) `fetch_kommatia()`: the two `STRING_AGG(...CONCAT(...))`
  subqueries (composer and lyricist name aggregation) swap `CONCAT(Eponymo, ' ', Onoma)` →
  `CONCAT(Onoma, ' ', Eponymo)`, so the piece list's "Συνθέτες"/"Στιχουργοί" columns show
  name-first.
- [views/xorodoi.py](../../../views/xorodoi.py): `display_cols` reorders to put "Onoma"
  before "Eponymo"; column_config labels stay attached to the same field, just reordered.
- [views/anafora_data.py](../../../views/anafora_data.py): Synthetes/Stixourgoi tables
  reorder displayed columns to Όνομα, Επώνυμο; the two add-forms put the Όνομα text input
  first; the delete-selectbox label lambdas use `person_label`.
- [views/kommatia.py](../../../views/kommatia.py): `_synthetis_label`/`_stixourgos_label`
  use `person_label`.
- [views/ekdiloseis.py](../../../views/ekdiloseis.py): `_atomo_label` uses `person_label`;
  the attendance data_editor's displayed columns reorder to Onoma, Eponymo.

**Not changed**: the underlying `ORDER BY Eponymo, Onoma` in `fetch_atoma()` and other
queries — sorting stays alphabetical-by-surname (confirmed with user, see §3), only the
*presentation* of the name reorders.

## 3. Χορωδοί: default sort + voice filter

### Schema change

`Foni` gets a new `SortOrder INT NOT NULL DEFAULT 0` column, editable from the
"Στοιχεία Αναφοράς" → Φωνές tab, so new voice sections added later get an explicit
position instead of a hardcoded mapping in Python.

Two SQL changes:
- [db/schema.sql](../../../db/schema.sql): add `SortOrder` to `CREATE TABLE dbo.Foni`,
  and populate it in the seed `INSERT` (Soprano=1, Baladeur=2, Alto=3). This file remains
  the drop-and-recreate fresh-install script.
- New **non-destructive** migration file `db/migrate_001_foni_sortorder.sql`, for the
  already-deployed database (which holds live member/event data — `schema.sql` cannot be
  re-run against it, it drops all tables). Adds the column with `ALTER TABLE ... ADD` only
  if not already present, then backfills `SortOrder` for the three known seed rows by
  `FoniSynt` ('S'→1, 'BAL'→2, 'A'→3), leaving any other existing custom voice rows at the
  default (0) — the user can then re-order them from the UI.

### database.py

- `fetch_foni()`: select `SortOrder` too; `ORDER BY SortOrder, FoniSynt` (keeps the
  reference-data tab showing voices in the same configured order).
- `add_foni`/`update_foni`: accept and persist `sort_order`.
- `fetch_atoma()`: also select `f.SortOrder AS FoniSortOrder` so the Xorodoi page can sort
  by it without a second query.

### views/xorodoi.py

- After building `df_atoma`, sort by `["FoniSortOrder", "Eponymo", "Onoma"]` before display
  (SQL already orders by Eponymo/Onoma so this is a stable re-sort by section).
- New `st.selectbox` "Φωνή" filter above the table: options = `["Όλες"]` + voice labels.
  Filtering narrows the *displayed* rows.
- **Correctness fix required**: the save handler currently computes
  `current_ids = set(df_atoma["AtomoID"])` (the full unfiltered set) and diffs against
  `edited_ids` to decide deletions. With a filter active, rows hidden by the filter would
  incorrectly be treated as deleted. Fix: compute `current_ids` from the *filtered* subset
  that was actually shown in the editor (`df_shown["AtomoID"]`), not the full `df_atoma`.

### views/anafora_data.py (Φωνές tab)

- Add `SortOrder` as an editable numeric column in the Foni data_editor (currently `FoniID`
  is hidden via `None` column_config — `SortOrder` becomes a visible, editable int column).

## 4. Πρόβες & Συναυλίες: filters

Both filters sit above "📋 Λίστα Προβών & Συναυλιών", narrowing `df_ekd` before the render
loop.

- **Type filter**: `st.segmented_control` with options `["Όλα", "Πρόβες", "Συναυλίες"]`
  (default "Όλα"), per project convention of preferring segmented_control over
  `st.radio(horizontal=True)`. Maps to `EventType` `'P'`/`'S'`.
- **Month/year filter**: single combined `st.selectbox`, options built from the distinct
  (year, month) pairs actually present in `df_ekd["Imerominia"]`, sorted descending, labeled
  with Greek month names + year (e.g. "Σεπτέμβριος 2026"), plus a leading "Όλοι" option.
  Greek month name list lives in `utils.py` (`GREEK_MONTHS`).

Both filters combine with AND logic on the already-fetched `df_ekd` (no new DB query
needed — the page already fetches the full event list).

## Testing

No test suite exists in this repo (confirmed in CLAUDE.md). Verification is manual: run
the app, exercise each of the 4 changes against live data.
