import os
import platform
import urllib.parse

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# Known machine -> SQL Server instance mappings. Add new machines here, or
# skip this entirely by setting the CHOIRAPP_DB_SERVER environment
# variable, which always takes priority. (Same pattern as MonthlyFood/db.py.)
KNOWN_SERVERS = {
    "SPEEDY": r"SPEEDY\SQLEXPRESS",
    "GEP-INTERNET": r"GEP-INTERNET\SQLEXPRESS",
}

DATABASE_NAME = "ChoirApp"


def _resolve_server():
    server = os.environ.get("CHOIRAPP_DB_SERVER")
    if server:
        return server
    current_pc = platform.node()
    return KNOWN_SERVERS.get(current_pc, f"{current_pc}\\SQLEXPRESS")


@st.cache_resource
def get_engine():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={_resolve_server()};"
        f"DATABASE={DATABASE_NAME};"
        "Trusted_Connection=yes;"
    )
    params = urllib.parse.quote_plus(conn_str)
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


def read_df(query, params=None):
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params=params)


def execute(query, params=None):
    with get_engine().begin() as conn:
        conn.execute(text(query), params or {})


# =========================================================================
# Foni
# =========================================================================

def fetch_foni():
    return read_df(
        "SELECT FoniID, FoniSynt, FoniDescr, SortOrder FROM Foni ORDER BY SortOrder, FoniSynt"
    )


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


def delete_foni(foni_id):
    execute("DELETE FROM Foni WHERE FoniID = :id", {"id": foni_id})


# =========================================================================
# Atomo
# =========================================================================

def fetch_atoma():
    query = """
        SELECT a.AtomoID, a.Eponymo, a.Onoma, a.KinitoTilefono,
               a.StatheroTilefono, a.Email, a.FoniID, f.FoniDescr, f.SortOrder AS FoniSortOrder
        FROM Atomo a
        LEFT JOIN Foni f ON a.FoniID = f.FoniID
        ORDER BY a.Eponymo, a.Onoma
    """
    return read_df(query)


def add_atomo(eponymo, onoma, kinito=None, statero=None, email=None, foni_id=None):
    execute(
        """
        INSERT INTO Atomo (Eponymo, Onoma, KinitoTilefono, StatheroTilefono, Email, FoniID)
        VALUES (:eponymo, :onoma, :kinito, :statero, :email, :foni_id)
        """,
        {"eponymo": eponymo, "onoma": onoma, "kinito": kinito,
         "statero": statero, "email": email, "foni_id": foni_id},
    )


def update_atomo(atomo_id, eponymo, onoma, kinito=None, statero=None, email=None, foni_id=None):
    execute(
        """
        UPDATE Atomo
        SET Eponymo = :eponymo, Onoma = :onoma, KinitoTilefono = :kinito,
            StatheroTilefono = :statero, Email = :email, FoniID = :foni_id
        WHERE AtomoID = :id
        """,
        {"eponymo": eponymo, "onoma": onoma, "kinito": kinito, "statero": statero,
         "email": email, "foni_id": foni_id, "id": atomo_id},
    )


def delete_atomo(atomo_id):
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM SymmetoxesEkdilosis WHERE AtomoID = :id"), {"id": atomo_id})
        conn.execute(text("DELETE FROM Atomo WHERE AtomoID = :id"), {"id": atomo_id})


# =========================================================================
# Synthetis / Stixourgos
# =========================================================================

def fetch_synthetes():
    return read_df(
        "SELECT SynthetisID, SynthetisEponymo, SynthetisOnoma FROM Synthetis ORDER BY SynthetisEponymo"
    )


def add_synthetis(eponymo, onoma=None):
    execute(
        "INSERT INTO Synthetis (SynthetisEponymo, SynthetisOnoma) VALUES (:eponymo, :onoma)",
        {"eponymo": eponymo, "onoma": onoma},
    )


def delete_synthetis(synthetis_id):
    execute("DELETE FROM Synthetis WHERE SynthetisID = :id", {"id": synthetis_id})


def fetch_stixourgoi():
    return read_df(
        "SELECT StixourgosID, StixourgosEponymo, StixourgosOnoma FROM Stixourgos ORDER BY StixourgosEponymo"
    )


def add_stixourgos(eponymo, onoma=None):
    execute(
        "INSERT INTO Stixourgos (StixourgosEponymo, StixourgosOnoma) VALUES (:eponymo, :onoma)",
        {"eponymo": eponymo, "onoma": onoma},
    )


def delete_stixourgos(stixourgos_id):
    execute("DELETE FROM Stixourgos WHERE StixourgosID = :id", {"id": stixourgos_id})


# =========================================================================
# Kommati (+ σύνθετες/στιχουργοί, πολλά-προς-πολλά)
# =========================================================================

def fetch_kommatia():
    query = """
        SELECT k.KommatiID, k.Titlos, k.Xronia, k.ExtraInfo,
               syn.Synthetes, sti.Stixourgoi
        FROM Kommati k
        LEFT JOIN (
            SELECT ks.KommatiID,
                   STRING_AGG(LTRIM(RTRIM(CONCAT(s.SynthetisOnoma, ' ', s.SynthetisEponymo))), ', ') AS Synthetes
            FROM KommatiaSynthetes ks
            JOIN Synthetis s ON ks.SynthetisID = s.SynthetisID
            GROUP BY ks.KommatiID
        ) syn ON syn.KommatiID = k.KommatiID
        LEFT JOIN (
            SELECT kst.KommatiID,
                   STRING_AGG(LTRIM(RTRIM(CONCAT(st.StixourgosOnoma, ' ', st.StixourgosEponymo))), ', ') AS Stixourgoi
            FROM KommatiaStixourgoi kst
            JOIN Stixourgos st ON kst.StixourgosID = st.StixourgosID
            GROUP BY kst.KommatiID
        ) sti ON sti.KommatiID = k.KommatiID
        ORDER BY k.Titlos
    """
    return read_df(query)


def fetch_kommati_links(kommati_id):
    synthetis_ids = read_df(
        "SELECT SynthetisID FROM KommatiaSynthetes WHERE KommatiID = :id", {"id": kommati_id}
    )["SynthetisID"].tolist()
    stixourgos_ids = read_df(
        "SELECT StixourgosID FROM KommatiaStixourgoi WHERE KommatiID = :id", {"id": kommati_id}
    )["StixourgosID"].tolist()
    return synthetis_ids, stixourgos_ids


def _set_kommati_links(conn, kommati_id, synthetis_ids, stixourgos_ids):
    conn.execute(text("DELETE FROM KommatiaSynthetes WHERE KommatiID = :id"), {"id": kommati_id})
    conn.execute(text("DELETE FROM KommatiaStixourgoi WHERE KommatiID = :id"), {"id": kommati_id})
    for synthetis_id in synthetis_ids:
        conn.execute(
            text("INSERT INTO KommatiaSynthetes (KommatiID, SynthetisID) VALUES (:kid, :sid)"),
            {"kid": kommati_id, "sid": synthetis_id},
        )
    for stixourgos_id in stixourgos_ids:
        conn.execute(
            text("INSERT INTO KommatiaStixourgoi (KommatiID, StixourgosID) VALUES (:kid, :sid)"),
            {"kid": kommati_id, "sid": stixourgos_id},
        )


def add_kommati(titlos, xronia=None, extra_info=None, synthetis_ids=None, stixourgos_ids=None):
    with get_engine().begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO Kommati (Titlos, Xronia, ExtraInfo) "
                "OUTPUT INSERTED.KommatiID VALUES (:titlos, :xronia, :extra)"
            ),
            {"titlos": titlos, "xronia": xronia, "extra": extra_info},
        )
        kommati_id = result.scalar()
        _set_kommati_links(conn, kommati_id, synthetis_ids or [], stixourgos_ids or [])
    return kommati_id


def update_kommati(kommati_id, titlos, xronia=None, extra_info=None, synthetis_ids=None, stixourgos_ids=None):
    with get_engine().begin() as conn:
        conn.execute(
            text("UPDATE Kommati SET Titlos = :titlos, Xronia = :xronia, ExtraInfo = :extra WHERE KommatiID = :id"),
            {"titlos": titlos, "xronia": xronia, "extra": extra_info, "id": kommati_id},
        )
        _set_kommati_links(conn, kommati_id, synthetis_ids or [], stixourgos_ids or [])


def delete_kommati(kommati_id):
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM KommatiaEkdilosis WHERE KommatiID = :id"), {"id": kommati_id})
        conn.execute(text("DELETE FROM KommatiaSynthetes WHERE KommatiID = :id"), {"id": kommati_id})
        conn.execute(text("DELETE FROM KommatiaStixourgoi WHERE KommatiID = :id"), {"id": kommati_id})
        conn.execute(text("DELETE FROM Kommati WHERE KommatiID = :id"), {"id": kommati_id})


# =========================================================================
# Ekdilosi (Prova / Synavlia)
# =========================================================================

def fetch_ekdiloseis():
    query = """
        SELECT e.EkdilosiID, e.EventType, e.Imerominia, e.ExtraInfo,
               s.Titlos, s.Xoros,
               (SELECT COUNT(*) FROM SymmetoxesEkdilosis se
                WHERE se.EkdilosiID = e.EkdilosiID AND se.Parousia = 1) AS ParousesCount,
               (SELECT COUNT(*) FROM KommatiaEkdilosis ke
                WHERE ke.EkdilosiID = e.EkdilosiID) AS KommatiaCount
        FROM Ekdilosi e
        LEFT JOIN Synavlia s ON e.EkdilosiID = s.EkdilosiID
        ORDER BY e.Imerominia DESC
    """
    return read_df(query)


def add_prova(imerominia, extra_info=None):
    with get_engine().begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO Ekdilosi (EventType, Imerominia, ExtraInfo) "
                "OUTPUT INSERTED.EkdilosiID VALUES ('P', :imerominia, :extra)"
            ),
            {"imerominia": imerominia, "extra": extra_info},
        )
        ekdilosi_id = result.scalar()
        conn.execute(text("INSERT INTO Prova (EkdilosiID) VALUES (:id)"), {"id": ekdilosi_id})
    return ekdilosi_id


def add_synavlia(imerominia, titlos, xoros=None, extra_info=None):
    with get_engine().begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO Ekdilosi (EventType, Imerominia, ExtraInfo) "
                "OUTPUT INSERTED.EkdilosiID VALUES ('S', :imerominia, :extra)"
            ),
            {"imerominia": imerominia, "extra": extra_info},
        )
        ekdilosi_id = result.scalar()
        conn.execute(
            text("INSERT INTO Synavlia (EkdilosiID, Titlos, Xoros) VALUES (:id, :titlos, :xoros)"),
            {"id": ekdilosi_id, "titlos": titlos, "xoros": xoros},
        )
    return ekdilosi_id


def delete_ekdilosi(ekdilosi_id):
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM SymmetoxesEkdilosis WHERE EkdilosiID = :id"), {"id": ekdilosi_id})
        conn.execute(text("DELETE FROM KommatiaEkdilosis WHERE EkdilosiID = :id"), {"id": ekdilosi_id})
        conn.execute(text("DELETE FROM Prova WHERE EkdilosiID = :id"), {"id": ekdilosi_id})
        conn.execute(text("DELETE FROM Synavlia WHERE EkdilosiID = :id"), {"id": ekdilosi_id})
        conn.execute(text("DELETE FROM Ekdilosi WHERE EkdilosiID = :id"), {"id": ekdilosi_id})


# =========================================================================
# Παρουσίες (SymmetoxesEkdilosis)
# =========================================================================

def fetch_symmetoxes(ekdilosi_id):
    query = """
        SELECT se.SymmetoxiID, se.AtomoID, a.Eponymo, a.Onoma, se.Parousia, se.ExtraInfo
        FROM SymmetoxesEkdilosis se
        JOIN Atomo a ON se.AtomoID = a.AtomoID
        WHERE se.EkdilosiID = :id
        ORDER BY a.Eponymo, a.Onoma
    """
    return read_df(query, {"id": ekdilosi_id})


def set_parousia(ekdilosi_id, atomo_id, parousia, extra_info=None):
    execute(
        """
        MERGE SymmetoxesEkdilosis AS target
        USING (SELECT :ekdilosi_id AS EkdilosiID, :atomo_id AS AtomoID) AS src
        ON target.EkdilosiID = src.EkdilosiID AND target.AtomoID = src.AtomoID
        WHEN MATCHED THEN
            UPDATE SET Parousia = :parousia, ExtraInfo = :extra
        WHEN NOT MATCHED THEN
            INSERT (EkdilosiID, AtomoID, Parousia, ExtraInfo)
            VALUES (:ekdilosi_id, :atomo_id, :parousia, :extra);
        """,
        {"ekdilosi_id": ekdilosi_id, "atomo_id": atomo_id, "parousia": parousia, "extra": extra_info},
    )


# =========================================================================
# Ρεπερτόριο ανά εκδήλωση (KommatiaEkdilosis)
# =========================================================================

def fetch_kommatia_ekdilosis(ekdilosi_id):
    query = """
        SELECT ke.KommatiEkdilosiID, ke.KommatiID, k.Titlos, ke.ExtraInfo
        FROM KommatiaEkdilosis ke
        JOIN Kommati k ON ke.KommatiID = k.KommatiID
        WHERE ke.EkdilosiID = :id
        ORDER BY k.Titlos
    """
    return read_df(query, {"id": ekdilosi_id})


def add_kommati_se_ekdilosi(ekdilosi_id, kommati_id, extra_info=None):
    execute(
        "INSERT INTO KommatiaEkdilosis (EkdilosiID, KommatiID, ExtraInfo) VALUES (:eid, :kid, :extra)",
        {"eid": ekdilosi_id, "kid": kommati_id, "extra": extra_info},
    )


def remove_kommati_apo_ekdilosi(ekdilosi_id, kommati_id):
    execute(
        "DELETE FROM KommatiaEkdilosis WHERE EkdilosiID = :eid AND KommatiID = :kid",
        {"eid": ekdilosi_id, "kid": kommati_id},
    )
