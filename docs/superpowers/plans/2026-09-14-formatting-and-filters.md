# Formatting & Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show dates as dd/mm/yy and full names as "Όνομα Επώνυμο" everywhere in the app, add a voice-section sort/filter to the Χορωδοί page, and add type + month/year filters to the Πρόβες & Συναυλίες page.

**Architecture:** Pure presentation-layer change plus one small schema addition (`Foni.SortOrder`). Two new shared display helpers live in a new `utils.py`. All SQL access stays in `database.py` (raw parameterized SQL via SQLAlchemy `text()`, no ORM — existing pattern). No new dependencies.

**Tech Stack:** Streamlit 1.58, pandas, SQLAlchemy + pyodbc, SQL Server.

## Global Constraints

- No test suite exists in this repo — every task's testing step is a manual run-the-app
  check, not automated tests (per spec §Testing).
- Preserve Greek domain naming (table/column/function names) — never translate identifiers.
- Use `width="stretch"`, never `use_container_width` (deprecated).
- Prefer `st.segmented_control` over `st.radio(horizontal=True)` for the event-type filter.
- Multi-statement DB writes stay wrapped in one `get_engine().begin()` transaction, matching
  existing functions in `database.py`.
- `db/schema.sql` remains the destructive drop-and-recreate fresh-install script — never
  run it against the live deployment. The live DB gets `SortOrder` via a **new**,
  non-destructive migration file.
- Spec: `docs/superpowers/specs/2026-09-14-formatting-and-filters-design.md`.

---

### Task 1: `utils.py` — shared display helpers

**Files:**
- Create: `utils.py`

**Interfaces:**
- Produces: `format_date(d) -> str`, `person_label(onoma, eponymo) -> str`,
  `GREEK_MONTHS: list[str]` (index 0 = Ιανουάριος ... index 11 = Δεκέμβριος).

- [ ] **Step 1: Create `utils.py`**

```python
"""Shared display helpers used across ChoirApp pages."""

import pandas as pd

GREEK_MONTHS = [
    "Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος",
    "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος",
]


def format_date(d):
    """Return a date/datetime as 'dd/mm/yy' for display. Empty string if missing."""
    if d is None or pd.isnull(d):
        return ""
    return d.strftime("%d/%m/%y")


def person_label(onoma, eponymo):
    """Return 'Onoma Eponymo' for display — name first, trimmed of stray whitespace."""
    return f"{onoma or ''} {eponymo or ''}".strip()
```

- [ ] **Step 2: Manually verify**

Run: `python -c "from utils import format_date, person_label, GREEK_MONTHS; import datetime; print(format_date(datetime.date(2026, 9, 14))); print(person_label('Γιώργος', 'Παπαδόπουλος')); print(GREEK_MONTHS[8])"`
Expected output:
```
14/09/26
Γιώργος Παπαδόπουλος
Σεπτέμβριος
```

- [ ] **Step 3: Commit**

```bash
git add utils.py
git commit -m "Add shared date/name display helpers

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: DB schema — `Foni.SortOrder`

**Files:**
- Modify: `db/schema.sql` (Foni table definition + seed INSERT)
- Create: `db/migrate_001_foni_sortorder.sql`

**Interfaces:**
- Produces: `Foni.SortOrder INT NOT NULL DEFAULT (0)` column, seeded 1/2/3 for
  Soprano/Baladeur/Alto on fresh installs and on the live DB after migration.

- [ ] **Step 1: Edit `db/schema.sql` — add the column**

Find:
```sql
CREATE TABLE dbo.Foni (
    FoniID      INT IDENTITY(1,1) NOT NULL,
    FoniSynt    NVARCHAR(20)      NOT NULL,   -- συντομογραφία, π.χ. "Σ1"
    FoniDescr   NVARCHAR(100)     NULL,       -- περιγραφή, π.χ. "Σοπράνο Α"
    CONSTRAINT PK_Foni PRIMARY KEY (FoniID)
);
GO
```

Replace with:
```sql
CREATE TABLE dbo.Foni (
    FoniID      INT IDENTITY(1,1) NOT NULL,
    FoniSynt    NVARCHAR(20)      NOT NULL,   -- συντομογραφία, π.χ. "Σ1"
    FoniDescr   NVARCHAR(100)     NULL,       -- περιγραφή, π.χ. "Σοπράνο Α"
    SortOrder   INT               NOT NULL DEFAULT (0),  -- σειρά εμφάνισης στα Χορωδοί
    CONSTRAINT PK_Foni PRIMARY KEY (FoniID)
);
GO
```

- [ ] **Step 2: Edit `db/schema.sql` — seed values**

Find:
```sql
INSERT INTO dbo.Foni (FoniSynt, FoniDescr) VALUES
    (N'S',   N'Soprano'),
    (N'A',   N'Alto'),
    (N'BAL', N'Baladeur');
GO
```

Replace with:
```sql
INSERT INTO dbo.Foni (FoniSynt, FoniDescr, SortOrder) VALUES
    (N'S',   N'Soprano',  1),
    (N'BAL', N'Baladeur', 2),
    (N'A',   N'Alto',     3);
GO
```

- [ ] **Step 3: Create `db/migrate_001_foni_sortorder.sql`**

```sql
/* =====================================================================
   Migration 001: προσθήκη Foni.SortOrder (μη destructive).

   Για την ήδη υπάρχουσα (live) βάση — schema.sql κάνει DROP/CREATE και
   δεν μπορεί να ξανατρέξει πάνω σε δεδομένα παραγωγής. Τρέξε αυτό το
   script μία φορά ανά deployment αντ' αυτού.
   ===================================================================== */

USE ChoirApp;
GO

IF COL_LENGTH('dbo.Foni', 'SortOrder') IS NULL
BEGIN
    ALTER TABLE dbo.Foni ADD SortOrder INT NOT NULL DEFAULT (0);
END
GO

UPDATE dbo.Foni
SET SortOrder = CASE FoniSynt
    WHEN N'S'   THEN 1
    WHEN N'BAL' THEN 2
    WHEN N'A'   THEN 3
    ELSE SortOrder
END
WHERE FoniSynt IN (N'S', N'BAL', N'A');
GO
```

- [ ] **Step 4: Manually verify**

Run the migration against the actual deployment server (adjust `-S` to the resolved
server, e.g. from `CHOIRAPP_DB_SERVER` or the `KNOWN_SERVERS` map in `database.py`):
```
sqlcmd -S <server> -i db\migrate_001_foni_sortorder.sql
sqlcmd -S <server> -d ChoirApp -Q "SELECT FoniSynt, FoniDescr, SortOrder FROM dbo.Foni ORDER BY SortOrder"
```
Expected: a `SortOrder` column exists; the three seed rows show `S=1, BAL=2, A=3`; any
other pre-existing custom voice rows show `SortOrder=0` and keep working (they just sort
last/first until reordered from the UI in Task 4).

- [ ] **Step 5: Commit**

```bash
git add db/schema.sql db/migrate_001_foni_sortorder.sql
git commit -m "Add Foni.SortOrder column and non-destructive migration

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: `database.py` — name-first queries + SortOrder plumbing

**Files:**
- Modify: `database.py:163-184` (`fetch_kommatia`), `database.py:54-69` (`fetch_foni`,
  `add_foni`, `update_foni`), `database.py:80-89` (`fetch_atoma`)

**Interfaces:**
- Consumes: `Foni.SortOrder` column (Task 2 must be applied to the DB you're running
  against before testing this task).
- Produces: `fetch_foni()` rows now include `SortOrder`; `add_foni(foni_synt, foni_descr=None, sort_order=0)`;
  `update_foni(foni_id, foni_synt, foni_descr=None, sort_order=0)`; `fetch_atoma()` rows
  now include `FoniSortOrder`.

- [ ] **Step 1: `fetch_kommatia()` — swap composer/lyricist name order**

Find (two occurrences, in the `syn` and `sti` subqueries):
```python
                   STRING_AGG(LTRIM(RTRIM(CONCAT(s.SynthetisEponymo, ' ', s.SynthetisOnoma))), ', ') AS Synthetes
```
Replace with:
```python
                   STRING_AGG(LTRIM(RTRIM(CONCAT(s.SynthetisOnoma, ' ', s.SynthetisEponymo))), ', ') AS Synthetes
```

Find:
```python
                   STRING_AGG(LTRIM(RTRIM(CONCAT(st.StixourgosEponymo, ' ', st.StixourgosOnoma))), ', ') AS Stixourgoi
```
Replace with:
```python
                   STRING_AGG(LTRIM(RTRIM(CONCAT(st.StixourgosOnoma, ' ', st.StixourgosEponymo))), ', ') AS Stixourgoi
```

- [ ] **Step 2: `fetch_foni()` — select and order by SortOrder**

Find:
```python
def fetch_foni():
    return read_df("SELECT FoniID, FoniSynt, FoniDescr FROM Foni ORDER BY FoniSynt")
```
Replace with:
```python
def fetch_foni():
    return read_df(
        "SELECT FoniID, FoniSynt, FoniDescr, SortOrder FROM Foni ORDER BY SortOrder, FoniSynt"
    )
```

- [ ] **Step 3: `add_foni` / `update_foni` — accept `sort_order`**

Find:
```python
def add_foni(foni_synt, foni_descr=None):
    execute(
        "INSERT INTO Foni (FoniSynt, FoniDescr) VALUES (:synt, :descr)",
        {"synt": foni_synt, "descr": foni_descr},
    )


def update_foni(foni_id, foni_synt, foni_descr=None):
    execute(
        "UPDATE Foni SET FoniSynt = :synt, FoniDescr = :descr WHERE FoniID = :id",
        {"synt": foni_synt, "descr": foni_descr, "id": foni_id},
    )
```
Replace with:
```python
def add_foni(foni_synt, foni_descr=None, sort_order=0):
    execute(
        "INSERT INTO Foni (FoniSynt, FoniDescr, SortOrder) VALUES (:synt, :descr, :sort_order)",
        {"synt": foni_synt, "descr": foni_descr, "sort_order": sort_order},
    )


def update_foni(foni_id, foni_synt, foni_descr=None, sort_order=0):
    execute(
        "UPDATE Foni SET FoniSynt = :synt, FoniDescr = :descr, SortOrder = :sort_order WHERE FoniID = :id",
        {"synt": foni_synt, "descr": foni_descr, "sort_order": sort_order, "id": foni_id},
    )
```

- [ ] **Step 4: `fetch_atoma()` — include `FoniSortOrder`**

Find:
```python
def fetch_atoma():
    query = """
        SELECT a.AtomoID, a.Eponymo, a.Onoma, a.KinitoTilefono,
               a.StatheroTilefono, a.Email, a.FoniID, f.FoniDescr
        FROM Atomo a
        LEFT JOIN Foni f ON a.FoniID = f.FoniID
        ORDER BY a.Eponymo, a.Onoma
    """
    return read_df(query)
```
Replace with:
```python
def fetch_atoma():
    query = """
        SELECT a.AtomoID, a.Eponymo, a.Onoma, a.KinitoTilefono,
               a.StatheroTilefono, a.Email, a.FoniID, f.FoniDescr, f.SortOrder AS FoniSortOrder
        FROM Atomo a
        LEFT JOIN Foni f ON a.FoniID = f.FoniID
        ORDER BY a.Eponymo, a.Onoma
    """
    return read_df(query)
```

- [ ] **Step 5: Manually verify**

Run: `python -c "import database; df = database.fetch_foni(); print(df); df2 = database.fetch_atoma(); print(df2.columns.tolist())"`
(Requires the DB from Task 2 to be reachable — same machine/server the app normally
connects to.)
Expected: `fetch_foni()` prints rows ordered Soprano, Baladeur, Alto (then any custom
voices) with a visible `SortOrder` column; `fetch_atoma()`'s column list includes
`FoniSortOrder`.

- [ ] **Step 6: Commit**

```bash
git add database.py
git commit -m "Query layer: name-first composer/lyricist strings, Foni.SortOrder support

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: `views/anafora_data.py` — SortOrder editor + name-first display

**Files:**
- Modify: `views/anafora_data.py` (imports; Φωνές tab; Συνθέτες tab; Στιχουργοί tab)

**Interfaces:**
- Consumes: `utils.person_label` (Task 1), `database.add_foni`/`update_foni` with
  `sort_order` (Task 3), `Foni.SortOrder` column present in the DB (Task 2).

- [ ] **Step 1: Add the import**

Find:
```python
import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError

from database import (
    add_foni,
    add_stixourgos,
    add_synthetis,
    delete_foni,
    delete_stixourgos,
    delete_synthetis,
    fetch_foni,
    fetch_stixourgoi,
    fetch_synthetes,
    update_foni,
)
```
Replace with:
```python
import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError

from database import (
    add_foni,
    add_stixourgos,
    add_synthetis,
    delete_foni,
    delete_stixourgos,
    delete_synthetis,
    fetch_foni,
    fetch_stixourgoi,
    fetch_synthetes,
    update_foni,
)
from utils import person_label
```

- [ ] **Step 2: Φωνές tab — editable `SortOrder` column**

Find:
```python
with tab_foni:
    df = fetch_foni()
    edited = st.data_editor(
        df,
        column_config={
            "FoniID": None,
            "FoniSynt": st.column_config.TextColumn("Συντομογραφία", required=True),
            "FoniDescr": st.column_config.TextColumn("Περιγραφή"),
        },
        num_rows="dynamic",
        width="stretch",
        key="foni_editor",
    )
    if st.button("💾 Αποθήκευση Φωνών"):
        current_ids = set(df["FoniID"])
        edited_ids = set(edited["FoniID"].dropna())
        try:
            for foni_id in current_ids - edited_ids:
                delete_foni(int(foni_id))
        except IntegrityError:
            st.error("Δεν μπορεί να διαγραφεί φωνή που χρησιμοποιείται ήδη από χορωδό.")
            st.stop()

        for _, row in edited.iterrows():
            if not row["FoniSynt"]:
                continue
            descr = None if pd.isnull(row["FoniDescr"]) else row["FoniDescr"]
            if pd.isnull(row["FoniID"]):
                add_foni(row["FoniSynt"], descr)
            else:
                update_foni(int(row["FoniID"]), row["FoniSynt"], descr)
        st.success("Οι φωνές αποθηκεύτηκαν!")
        st.rerun()
```
Replace with:
```python
with tab_foni:
    df = fetch_foni()
    edited = st.data_editor(
        df,
        column_config={
            "FoniID": None,
            "FoniSynt": st.column_config.TextColumn("Συντομογραφία", required=True),
            "FoniDescr": st.column_config.TextColumn("Περιγραφή"),
            "SortOrder": st.column_config.NumberColumn(
                "Σειρά ταξινόμησης", step=1, default=0
            ),
        },
        num_rows="dynamic",
        width="stretch",
        key="foni_editor",
    )
    if st.button("💾 Αποθήκευση Φωνών"):
        current_ids = set(df["FoniID"])
        edited_ids = set(edited["FoniID"].dropna())
        try:
            for foni_id in current_ids - edited_ids:
                delete_foni(int(foni_id))
        except IntegrityError:
            st.error("Δεν μπορεί να διαγραφεί φωνή που χρησιμοποιείται ήδη από χορωδό.")
            st.stop()

        for _, row in edited.iterrows():
            if not row["FoniSynt"]:
                continue
            descr = None if pd.isnull(row["FoniDescr"]) else row["FoniDescr"]
            sort_order = 0 if pd.isnull(row["SortOrder"]) else int(row["SortOrder"])
            if pd.isnull(row["FoniID"]):
                add_foni(row["FoniSynt"], descr, sort_order)
            else:
                update_foni(int(row["FoniID"]), row["FoniSynt"], descr, sort_order)
        st.success("Οι φωνές αποθηκεύτηκαν!")
        st.rerun()
```

- [ ] **Step 3: Συνθέτες tab — name-first table, form, delete label**

Find:
```python
with tab_synthetes:
    df = fetch_synthetes()
    st.dataframe(
        df.rename(columns={"SynthetisEponymo": "Επώνυμο", "SynthetisOnoma": "Όνομα"})[["Επώνυμο", "Όνομα"]],
        width="stretch",
        hide_index=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        new_eponymo = st.text_input("Επώνυμο Συνθέτη")
    with col2:
        new_onoma = st.text_input("Όνομα Συνθέτη")
    if st.button("➕ Προσθήκη Συνθέτη", disabled=not new_eponymo):
        add_synthetis(new_eponymo, new_onoma or None)
        st.success("Ο συνθέτης προστέθηκε!")
        st.rerun()

    if not df.empty:
        label = lambda r: f"{r['SynthetisEponymo']} {r['SynthetisOnoma'] or ''}".strip()
        options = {label(row): row["SynthetisID"] for _, row in df.iterrows()}
        to_delete = st.selectbox("Διαγραφή συνθέτη:", list(options.keys()), key="del_synthetis_sb")
        if st.button("🗑️ Διαγραφή Συνθέτη"):
            try:
                delete_synthetis(options[to_delete])
                st.success("Ο συνθέτης διαγράφηκε!")
                st.rerun()
            except IntegrityError:
                st.error("Δεν μπορεί να διαγραφεί — ο συνθέτης χρησιμοποιείται σε κάποιο κομμάτι.")
```
Replace with:
```python
with tab_synthetes:
    df = fetch_synthetes()
    st.dataframe(
        df.rename(columns={"SynthetisEponymo": "Επώνυμο", "SynthetisOnoma": "Όνομα"})[["Όνομα", "Επώνυμο"]],
        width="stretch",
        hide_index=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        new_onoma = st.text_input("Όνομα Συνθέτη")
    with col2:
        new_eponymo = st.text_input("Επώνυμο Συνθέτη")
    if st.button("➕ Προσθήκη Συνθέτη", disabled=not new_eponymo):
        add_synthetis(new_eponymo, new_onoma or None)
        st.success("Ο συνθέτης προστέθηκε!")
        st.rerun()

    if not df.empty:
        options = {
            person_label(row["SynthetisOnoma"], row["SynthetisEponymo"]): row["SynthetisID"]
            for _, row in df.iterrows()
        }
        to_delete = st.selectbox("Διαγραφή συνθέτη:", list(options.keys()), key="del_synthetis_sb")
        if st.button("🗑️ Διαγραφή Συνθέτη"):
            try:
                delete_synthetis(options[to_delete])
                st.success("Ο συνθέτης διαγράφηκε!")
                st.rerun()
            except IntegrityError:
                st.error("Δεν μπορεί να διαγραφεί — ο συνθέτης χρησιμοποιείται σε κάποιο κομμάτι.")
```

- [ ] **Step 4: Στιχουργοί tab — same treatment**

Find:
```python
with tab_stixourgoi:
    df = fetch_stixourgoi()
    st.dataframe(
        df.rename(columns={"StixourgosEponymo": "Επώνυμο", "StixourgosOnoma": "Όνομα"})[["Επώνυμο", "Όνομα"]],
        width="stretch",
        hide_index=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        new_eponymo = st.text_input("Επώνυμο Στιχουργού")
    with col2:
        new_onoma = st.text_input("Όνομα Στιχουργού")
    if st.button("➕ Προσθήκη Στιχουργού", disabled=not new_eponymo):
        add_stixourgos(new_eponymo, new_onoma or None)
        st.success("Ο στιχουργός προστέθηκε!")
        st.rerun()

    if not df.empty:
        label = lambda r: f"{r['StixourgosEponymo']} {r['StixourgosOnoma'] or ''}".strip()
        options = {label(row): row["StixourgosID"] for _, row in df.iterrows()}
        to_delete = st.selectbox("Διαγραφή στιχουργού:", list(options.keys()), key="del_stixourgos_sb")
        if st.button("🗑️ Διαγραφή Στιχουργού"):
            try:
                delete_stixourgos(options[to_delete])
                st.success("Ο στιχουργός διαγράφηκε!")
                st.rerun()
            except IntegrityError:
                st.error("Δεν μπορεί να διαγραφεί — ο στιχουργός χρησιμοποιείται σε κάποιο κομμάτι.")
```
Replace with:
```python
with tab_stixourgoi:
    df = fetch_stixourgoi()
    st.dataframe(
        df.rename(columns={"StixourgosEponymo": "Επώνυμο", "StixourgosOnoma": "Όνομα"})[["Όνομα", "Επώνυμο"]],
        width="stretch",
        hide_index=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        new_onoma = st.text_input("Όνομα Στιχουργού")
    with col2:
        new_eponymo = st.text_input("Επώνυμο Στιχουργού")
    if st.button("➕ Προσθήκη Στιχουργού", disabled=not new_eponymo):
        add_stixourgos(new_eponymo, new_onoma or None)
        st.success("Ο στιχουργός προστέθηκε!")
        st.rerun()

    if not df.empty:
        options = {
            person_label(row["StixourgosOnoma"], row["StixourgosEponymo"]): row["StixourgosID"]
            for _, row in df.iterrows()
        }
        to_delete = st.selectbox("Διαγραφή στιχουργού:", list(options.keys()), key="del_stixourgos_sb")
        if st.button("🗑️ Διαγραφή Στιχουργού"):
            try:
                delete_stixourgos(options[to_delete])
                st.success("Ο στιχουργός διαγράφηκε!")
                st.rerun()
            except IntegrityError:
                st.error("Δεν μπορεί να διαγραφεί — ο στιχουργός χρησιμοποιείται σε κάποιο κομμάτι.")
```

- [ ] **Step 5: Manually verify**

Run: `streamlit run ChoirApp.py`, open "Στοιχεία Αναφοράς".
Expected: Φωνές tab shows an editable "Σειρά ταξινόμησης" column; editing it and saving
persists (reload the page, value sticks). Συνθέτες/Στιχουργοί tables show Όνομα before
Επώνυμο; the add-forms have the Όνομα field first; adding one and then using the delete
dropdown shows "Όνομα Επώνυμο" in the option list.

- [ ] **Step 6: Commit**

```bash
git add views/anafora_data.py
git commit -m "Reference data page: editable Foni sort order, name-first display

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: `views/kommatia.py` — name-first composer/lyricist labels

**Files:**
- Modify: `views/kommatia.py:1-44`

**Interfaces:**
- Consumes: `utils.person_label` (Task 1).

- [ ] **Step 1: Add the import**

Find:
```python
import pandas as pd
import streamlit as st

from database import (
    add_kommati,
    delete_kommati,
    fetch_kommati_links,
    fetch_kommatia,
    fetch_stixourgoi,
    fetch_synthetes,
    update_kommati,
)
```
Replace with:
```python
import pandas as pd
import streamlit as st

from database import (
    add_kommati,
    delete_kommati,
    fetch_kommati_links,
    fetch_kommatia,
    fetch_stixourgoi,
    fetch_synthetes,
    update_kommati,
)
from utils import person_label
```

- [ ] **Step 2: Use `person_label` in the two label helpers**

Find:
```python
def _synthetis_label(row):
    return f"{row['SynthetisEponymo']} {row['SynthetisOnoma'] or ''}".strip()


def _stixourgos_label(row):
    return f"{row['StixourgosEponymo']} {row['StixourgosOnoma'] or ''}".strip()
```
Replace with:
```python
def _synthetis_label(row):
    return person_label(row["SynthetisOnoma"], row["SynthetisEponymo"])


def _stixourgos_label(row):
    return person_label(row["StixourgosOnoma"], row["StixourgosEponymo"])
```

- [ ] **Step 3: Manually verify**

Run: `streamlit run ChoirApp.py`, open "Μουσικά Κομμάτια".
Expected: the read-only list's "Συνθέτες"/"Στιχουργοί" columns show "Όνομα Επώνυμο"
(this also depends on Task 3's `fetch_kommatia` CONCAT swap being applied); the
Συνθέτες/Στιχουργοί multiselect options below show "Όνομα Επώνυμο" too.

- [ ] **Step 4: Commit**

```bash
git add views/kommatia.py
git commit -m "Pieces page: name-first composer/lyricist labels

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 6: `views/xorodoi.py` — sort, filter, name-first columns, diff-bug fix

**Files:**
- Modify: `views/xorodoi.py` (whole file — small enough to replace in full)

**Interfaces:**
- Consumes: `fetch_atoma()` rows carrying `FoniSortOrder` (Task 3).

- [ ] **Step 1: Replace the full file**

Find (entire current file):
```python
import pandas as pd
import streamlit as st

from database import add_atomo, delete_atomo, fetch_atoma, fetch_foni, update_atomo

st.title("🧑‍🤝‍🧑 Χορωδοί")


def _clean(value):
    return None if pd.isnull(value) else value


df_foni = fetch_foni()
foni_options = {
    (row["FoniDescr"] or row["FoniSynt"]): row["FoniID"] for _, row in df_foni.iterrows()
}
foni_id_to_label = {v: k for k, v in foni_options.items()}

df_atoma = fetch_atoma()
df_atoma["Φωνή"] = df_atoma["FoniID"].map(foni_id_to_label)

display_cols = ["AtomoID", "Eponymo", "Onoma", "Φωνή", "KinitoTilefono", "StatheroTilefono", "Email"]

edited = st.data_editor(
    df_atoma[display_cols],
    column_config={
        "AtomoID": None,
        "Eponymo": st.column_config.TextColumn("Επώνυμο", required=True),
        "Onoma": st.column_config.TextColumn("Όνομα", required=True),
        "Φωνή": st.column_config.SelectboxColumn("Φωνή", options=list(foni_options.keys())),
        "KinitoTilefono": st.column_config.TextColumn("Κινητό"),
        "StatheroTilefono": st.column_config.TextColumn("Σταθερό"),
        "Email": st.column_config.TextColumn("Email"),
    },
    num_rows="dynamic",
    width="stretch",
    key="atoma_editor",
)

if st.button("💾 Αποθήκευση Αλλαγών"):
    current_ids = set(df_atoma["AtomoID"])
    edited_ids = set(edited["AtomoID"].dropna())

    for atomo_id in current_ids - edited_ids:
        delete_atomo(int(atomo_id))

    for _, row in edited.iterrows():
        if not row["Eponymo"] or not row["Onoma"]:
            continue
        foni_id = foni_options.get(row["Φωνή"])
        args = (row["Eponymo"], row["Onoma"], _clean(row["KinitoTilefono"]),
                 _clean(row["StatheroTilefono"]), _clean(row["Email"]), foni_id)
        if pd.isnull(row["AtomoID"]):
            add_atomo(*args)
        else:
            update_atomo(int(row["AtomoID"]), *args)

    st.success("Οι αλλαγές αποθηκεύτηκαν!")
    st.rerun()
```

Replace with:
```python
import pandas as pd
import streamlit as st

from database import add_atomo, delete_atomo, fetch_atoma, fetch_foni, update_atomo

st.title("🧑‍🤝‍🧑 Χορωδοί")


def _clean(value):
    return None if pd.isnull(value) else value


df_foni = fetch_foni()
foni_options = {
    (row["FoniDescr"] or row["FoniSynt"]): row["FoniID"] for _, row in df_foni.iterrows()
}
foni_id_to_label = {v: k for k, v in foni_options.items()}

df_atoma = fetch_atoma()
df_atoma["Φωνή"] = df_atoma["FoniID"].map(foni_id_to_label)
df_atoma = df_atoma.sort_values(
    by=["FoniSortOrder", "Eponymo", "Onoma"], na_position="last"
).reset_index(drop=True)

foni_filter = st.selectbox("Φίλτρο φωνής", ["Όλες"] + list(foni_options.keys()))
df_shown = df_atoma if foni_filter == "Όλες" else df_atoma[df_atoma["Φωνή"] == foni_filter]

display_cols = ["AtomoID", "Onoma", "Eponymo", "Φωνή", "KinitoTilefono", "StatheroTilefono", "Email"]

edited = st.data_editor(
    df_shown[display_cols],
    column_config={
        "AtomoID": None,
        "Onoma": st.column_config.TextColumn("Όνομα", required=True),
        "Eponymo": st.column_config.TextColumn("Επώνυμο", required=True),
        "Φωνή": st.column_config.SelectboxColumn("Φωνή", options=list(foni_options.keys())),
        "KinitoTilefono": st.column_config.TextColumn("Κινητό"),
        "StatheroTilefono": st.column_config.TextColumn("Σταθερό"),
        "Email": st.column_config.TextColumn("Email"),
    },
    num_rows="dynamic",
    width="stretch",
    key="atoma_editor",
)

if st.button("💾 Αποθήκευση Αλλαγών"):
    current_ids = set(df_shown["AtomoID"])
    edited_ids = set(edited["AtomoID"].dropna())

    for atomo_id in current_ids - edited_ids:
        delete_atomo(int(atomo_id))

    for _, row in edited.iterrows():
        if not row["Eponymo"] or not row["Onoma"]:
            continue
        foni_id = foni_options.get(row["Φωνή"])
        args = (row["Eponymo"], row["Onoma"], _clean(row["KinitoTilefono"]),
                 _clean(row["StatheroTilefono"]), _clean(row["Email"]), foni_id)
        if pd.isnull(row["AtomoID"]):
            add_atomo(*args)
        else:
            update_atomo(int(row["AtomoID"]), *args)

    st.success("Οι αλλαγές αποθηκεύτηκαν!")
    st.rerun()
```

- [ ] **Step 2: Manually verify**

Run: `streamlit run ChoirApp.py`, open "Χορωδοί".
Expected: table columns show Όνομα before Επώνυμο; with the "Φίλτρο φωνής" left on "Όλες",
rows appear grouped Soprano, then Baladeur, then Alto, alphabetical-by-Επώνυμο within each
group. Pick a specific voice in the filter — only that group's members show. **With the
filter narrowed to one voice**, click "💾 Αποθήκευση Αλλαγών" without changing anything —
reload and confirm members of the *other* voices are still present (this is the diff-bug
fix: it must NOT have deleted the hidden rows).

- [ ] **Step 3: Commit**

```bash
git add views/xorodoi.py
git commit -m "Choir members page: sort by voice+surname, add voice filter

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: `views/ekdiloseis.py` — dates, name-first, type + month/year filters

**Files:**
- Modify: `views/ekdiloseis.py` (imports; `_atomo_label`; new-event dialog date input;
  view dialog subheader + attendance table; list section)

**Interfaces:**
- Consumes: `utils.format_date`, `utils.person_label`, `utils.GREEK_MONTHS` (Task 1).

- [ ] **Step 1: Imports + `_atomo_label`**

Find:
```python
import pandas as pd
import streamlit as st

from database import (
    add_kommati_se_ekdilosi,
    add_prova,
    add_synavlia,
    delete_ekdilosi,
    fetch_atoma,
    fetch_ekdiloseis,
    fetch_kommatia,
    fetch_kommatia_ekdilosis,
    fetch_symmetoxes,
    remove_kommati_apo_ekdilosi,
    set_parousia,
)

st.title("📅 Πρόβες & Συναυλίες")


def _atomo_label(row):
    return f"{row['Eponymo']} {row['Onoma']}"
```
Replace with:
```python
import pandas as pd
import streamlit as st

from database import (
    add_kommati_se_ekdilosi,
    add_prova,
    add_synavlia,
    delete_ekdilosi,
    fetch_atoma,
    fetch_ekdiloseis,
    fetch_kommatia,
    fetch_kommatia_ekdilosis,
    fetch_symmetoxes,
    remove_kommati_apo_ekdilosi,
    set_parousia,
)
from utils import GREEK_MONTHS, format_date, person_label

st.title("📅 Πρόβες & Συναυλίες")


def _atomo_label(row):
    return person_label(row["Onoma"], row["Eponymo"])
```

- [ ] **Step 2: Date input format**

Find:
```python
    col1, col2 = st.columns(2)
    with col1:
        imerominia = st.date_input("Ημερομηνία")
    with col2:
        titlos = st.text_input("Τίτλος Συναυλίας") if event_type == "Συναυλία" else None
```
Replace with:
```python
    col1, col2 = st.columns(2)
    with col1:
        imerominia = st.date_input("Ημερομηνία", format="DD/MM/YYYY")
    with col2:
        titlos = st.text_input("Τίτλος Συναυλίας") if event_type == "Συναυλία" else None
```

- [ ] **Step 3: View dialog subheader date**

Find:
```python
    kind = "Πρόβα" if row["EventType"] == "P" else "Συναυλία"
    st.subheader(f"{kind} — {row['Imerominia'].strftime('%d/%m/%Y')}")
```
Replace with:
```python
    kind = "Πρόβα" if row["EventType"] == "P" else "Συναυλία"
    st.subheader(f"{kind} — {format_date(row['Imerominia'])}")
```

- [ ] **Step 4: Attendance table — name-first columns**

Find:
```python
            df_view = df_atoma[["AtomoID", "Eponymo", "Onoma"]].copy()
            df_view["Συμμετείχε"] = df_view["AtomoID"].map(lambda x: bool(parousia_map.get(x, False)))

            edited = st.data_editor(
                df_view,
                column_config={
                    "AtomoID": None,
                    "Eponymo": st.column_config.TextColumn("Επώνυμο", disabled=True),
                    "Onoma": st.column_config.TextColumn("Όνομα", disabled=True),
                    "Συμμετείχε": st.column_config.CheckboxColumn("Συμμετείχε"),
                },
                hide_index=True,
                width="stretch",
                key=f"view_parousies_{ekdilosi_id}",
            )
```
Replace with:
```python
            df_view = df_atoma[["AtomoID", "Onoma", "Eponymo"]].copy()
            df_view["Συμμετείχε"] = df_view["AtomoID"].map(lambda x: bool(parousia_map.get(x, False)))

            edited = st.data_editor(
                df_view,
                column_config={
                    "AtomoID": None,
                    "Onoma": st.column_config.TextColumn("Όνομα", disabled=True),
                    "Eponymo": st.column_config.TextColumn("Επώνυμο", disabled=True),
                    "Συμμετείχε": st.column_config.CheckboxColumn("Συμμετείχε"),
                },
                hide_index=True,
                width="stretch",
                key=f"view_parousies_{ekdilosi_id}",
            )
```

- [ ] **Step 5: List section — add filters, use `format_date`**

Find:
```python
if st.button("➕ Εισαγωγή Πρόβας / Συναυλίας"):
    new_ekdilosi_dialog()

st.divider()
st.subheader("📋 Λίστα Προβών & Συναυλιών")

df_ekd = fetch_ekdiloseis()

if df_ekd.empty:
    st.info("Δεν υπάρχουν ακόμα εκδηλώσεις.")
else:
    for _, row in df_ekd.iterrows():
        with st.container(border=True):
            cols = st.columns([1.3, 1.3, 2.5, 2, 1.4, 1.2, 1.4])
            kind_icon = "🎤" if row["EventType"] == "P" else "🎭"
            kind = "Πρόβα" if row["EventType"] == "P" else "Συναυλία"
            cols[0].markdown(f"{kind_icon} **{kind}**")
            cols[1].write(row["Imerominia"].strftime("%d/%m/%Y"))
            cols[2].write(row["Titlos"] if pd.notnull(row["Titlos"]) else "—")
            cols[3].write(row["Xoros"] if pd.notnull(row["Xoros"]) else "—")
            cols[4].write(f"👥 {int(row['ParousesCount'])}")
            cols[5].write(f"🎼 {int(row['KommatiaCount'])}")
            if cols[6].button("🔍 Προβολή", key=f"view_{row['EkdilosiID']}", width="stretch"):
                view_ekdilosi_dialog(int(row["EkdilosiID"]), row)
```
Replace with:
```python
if st.button("➕ Εισαγωγή Πρόβας / Συναυλίας"):
    new_ekdilosi_dialog()

st.divider()
st.subheader("📋 Λίστα Προβών & Συναυλιών")

df_ekd = fetch_ekdiloseis()

type_filter = st.segmented_control(
    "Τύπος", ["Όλα", "Πρόβες", "Συναυλίες"], default="Όλα", key="ekd_type_filter"
)

month_options = ["Όλοι"]
if not df_ekd.empty:
    periods = sorted({(d.year, d.month) for d in df_ekd["Imerominia"]}, reverse=True)
    month_options += [f"{GREEK_MONTHS[m - 1]} {y}" for y, m in periods]
month_filter = st.selectbox("Μήνας", month_options, key="ekd_month_filter")

df_shown = df_ekd
if type_filter == "Πρόβες":
    df_shown = df_shown[df_shown["EventType"] == "P"]
elif type_filter == "Συναυλίες":
    df_shown = df_shown[df_shown["EventType"] == "S"]
if month_filter != "Όλοι":
    month_name, year_str = month_filter.rsplit(" ", 1)
    month_num = GREEK_MONTHS.index(month_name) + 1
    year_num = int(year_str)
    df_shown = df_shown[
        (df_shown["Imerominia"].apply(lambda d: d.year) == year_num)
        & (df_shown["Imerominia"].apply(lambda d: d.month) == month_num)
    ]

if df_shown.empty:
    st.info("Δεν υπάρχουν εκδηλώσεις για τα επιλεγμένα φίλτρα.")
else:
    for _, row in df_shown.iterrows():
        with st.container(border=True):
            cols = st.columns([1.3, 1.3, 2.5, 2, 1.4, 1.2, 1.4])
            kind_icon = "🎤" if row["EventType"] == "P" else "🎭"
            kind = "Πρόβα" if row["EventType"] == "P" else "Συναυλία"
            cols[0].markdown(f"{kind_icon} **{kind}**")
            cols[1].write(format_date(row["Imerominia"]))
            cols[2].write(row["Titlos"] if pd.notnull(row["Titlos"]) else "—")
            cols[3].write(row["Xoros"] if pd.notnull(row["Xoros"]) else "—")
            cols[4].write(f"👥 {int(row['ParousesCount'])}")
            cols[5].write(f"🎼 {int(row['KommatiaCount'])}")
            if cols[6].button("🔍 Προβολή", key=f"view_{row['EkdilosiID']}", width="stretch"):
                view_ekdilosi_dialog(int(row["EkdilosiID"]), row)
```

- [ ] **Step 6: Manually verify**

Run: `streamlit run ChoirApp.py`, open "Πρόβες & Συναυλίες".
Expected: dates in the list and in an event's detail dialog show as `dd/mm/yy`; the
new-event date picker shows a 4-digit-year calendar in `DD/MM/YYYY` order (documented
widget limitation — see spec §1); the attendance multiselect and table show "Όνομα
Επώνυμο"; the segmented control filters the list to only rehearsals / only concerts /
all; the month/year dropdown (built from actual event dates) narrows the list further,
and combining both filters works (e.g. "Πρόβες" + a specific month shows only that
month's rehearsals).

- [ ] **Step 7: Commit**

```bash
git add views/ekdiloseis.py
git commit -m "Events page: dd/mm/yy dates, name-first labels, type + month filters

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Self-Review Notes

- **Spec coverage**: §1 dates → Task 7 (display) + date_input format, documented widget
  4-digit-year limitation. §2 name-first → Tasks 1, 3–7 cover every concatenation point and
  every data_editor/dataframe column order identified in the spec. §3 Xorodoi sort/filter +
  SortOrder → Tasks 2, 3, 6, with the diff-bug fix called out explicitly. §4 Ekdiloseis
  filters → Task 7 Step 5.
- **Placeholder scan**: none — every step has full code or an exact runnable command.
- **Type consistency**: `add_foni`/`update_foni` signatures in Task 3 match the call sites
  added in Task 4; `person_label(onoma, eponymo)` parameter order matches every call site
  across Tasks 4/5/7; `GREEK_MONTHS` index convention (0-based, Ιανουάριος first) matches
  its one use site in Task 7.
