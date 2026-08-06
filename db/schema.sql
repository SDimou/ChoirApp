/* =====================================================================
   ChoirApp — Πλήρες σχήμα βάσης (SQL Server)
   =====================================================================

   Σχεδιαστικές αποφάσεις:

   1) Prova / Synavlia:
      Κοινός "βασικός" πίνακας Ekdilosi (EventType 'P'=Πρόβα, 'S'=Συναυλία)
      + δύο πίνακες υποτύπων (Prova, Synavlia) για τα ειδικά πεδία τους.
      Το ζευγάρι FOREIGN KEY (EkdilosiID, EventType) εξασφαλίζει ότι μια
      εγγραφή Synavlia δεν μπορεί ποτέ να δείξει σε Ekdilosi τύπου 'P'
      (και αντίστροφα) — χωρίς triggers, μόνο με constraints.

   2) Kommati -> Synthetis / Stixourgos:
      Μετατράπηκαν από 1-προς-πολλά σε πολλά-προς-πολλά (ένα κομμάτι
      μπορεί να έχει πάνω από έναν συνθέτη ή στιχουργό, π.χ. συνεργασίες),
      μέσω των συνδετικών πινάκων KommatiaSynthetes / KommatiaStixourgoi.

   3) Ενοποιημένοι συνδετικοί πίνακες πάνω στο Ekdilosi:
      - SymmetoxesEkdilosis: παρουσίες ατόμων σε πρόβες/συναυλίες
      - KommatiaEkdilosis:   ρεπερτόριο (ποια κομμάτια παίχτηκαν/
                              δουλεύτηκαν σε ποια εκδήλωση)
      Έτσι δεν χρειάζονται πλέον ξεχωριστά ζεύγη πινάκων για Prova/Synavlia.

   Σειρά δημιουργίας: σέβεται τις εξαρτήσεις FOREIGN KEY.
   ===================================================================== */

SET NOCOUNT ON;
GO

/* ---------------------------------------------------------------------
   Δημιουργία βάσης
   --------------------------------------------------------------------- */
IF DB_ID(N'ChoirApp') IS NULL
BEGIN
    CREATE DATABASE ChoirApp;
END
GO

USE ChoirApp;
GO

/* ---------------------------------------------------------------------
   Καθαρισμός (επιτρέπει την επανεκτέλεση του script από την αρχή)
   Σειρά: αντίστροφη από τις εξαρτήσεις FOREIGN KEY.
   --------------------------------------------------------------------- */
DROP TABLE IF EXISTS dbo.KommatiaEkdilosis;
DROP TABLE IF EXISTS dbo.KommatiaStixourgoi;
DROP TABLE IF EXISTS dbo.KommatiaSynthetes;
DROP TABLE IF EXISTS dbo.Kommati;
DROP TABLE IF EXISTS dbo.Stixourgos;
DROP TABLE IF EXISTS dbo.Synthetis;
DROP TABLE IF EXISTS dbo.SymmetoxesEkdilosis;
DROP TABLE IF EXISTS dbo.Synavlia;
DROP TABLE IF EXISTS dbo.Prova;
DROP TABLE IF EXISTS dbo.Ekdilosi;
DROP TABLE IF EXISTS dbo.Atomo;
DROP TABLE IF EXISTS dbo.Foni;
GO

/* ---------------------------------------------------------------------
   Foni (Φωνητικό τμήμα, π.χ. Σοπράνο, Άλτο, Τενόρος, Μπάσος)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.Foni (
    FoniID      INT IDENTITY(1,1) NOT NULL,
    FoniSynt    NVARCHAR(20)      NOT NULL,   -- συντομογραφία, π.χ. "Σ1"
    FoniDescr   NVARCHAR(100)     NULL,       -- περιγραφή, π.χ. "Σοπράνο Α"
    CONSTRAINT PK_Foni PRIMARY KEY (FoniID)
);
GO

/* ---------------------------------------------------------------------
   Atomo (Μέλος χορωδίας)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.Atomo (
    AtomoID             INT IDENTITY(1,1) NOT NULL,
    Eponymo             NVARCHAR(100)     NOT NULL,
    Onoma               NVARCHAR(100)     NOT NULL,
    KinitoTilefono      NVARCHAR(20)      NULL,
    StatheroTilefono    NVARCHAR(20)      NULL,
    FoniID              INT               NULL,
    Email               NVARCHAR(200)     NULL,
    CONSTRAINT PK_Atomo PRIMARY KEY (AtomoID),
    CONSTRAINT FK_Atomo_Foni FOREIGN KEY (FoniID)
        REFERENCES dbo.Foni (FoniID)
);
GO

CREATE INDEX IX_Atomo_FoniID ON dbo.Atomo (FoniID);
GO

/* ---------------------------------------------------------------------
   Ekdilosi (βασικός πίνακας: Πρόβα ή Συναυλία)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.Ekdilosi (
    EkdilosiID  INT IDENTITY(1,1) NOT NULL,
    EventType   CHAR(1)           NOT NULL,   -- 'P' = Πρόβα, 'S' = Συναυλία
    Imerominia  DATE              NOT NULL,
    ExtraInfo   NVARCHAR(1000)    NULL,
    CONSTRAINT PK_Ekdilosi PRIMARY KEY (EkdilosiID),
    CONSTRAINT CK_Ekdilosi_EventType CHECK (EventType IN ('P', 'S')),
    -- Επιτρέπει στους υποτύπους (Prova/Synavlia) να κάνουν FK σε (ID, Type)
    CONSTRAINT UQ_Ekdilosi_ID_Type UNIQUE (EkdilosiID, EventType)
);
GO

CREATE INDEX IX_Ekdilosi_Imerominia ON dbo.Ekdilosi (Imerominia);
GO

/* ---------------------------------------------------------------------
   Prova (υπότυπος Ekdilosi — ειδικά πεδία πρόβας, αν/όταν χρειαστούν)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.Prova (
    EkdilosiID  INT NOT NULL,
    EventType   AS (CAST('P' AS CHAR(1))) PERSISTED,
    CONSTRAINT PK_Prova PRIMARY KEY (EkdilosiID),
    CONSTRAINT FK_Prova_Ekdilosi FOREIGN KEY (EkdilosiID, EventType)
        REFERENCES dbo.Ekdilosi (EkdilosiID, EventType)
);
GO

/* ---------------------------------------------------------------------
   Synavlia (υπότυπος Ekdilosi — ειδικά πεδία συναυλίας)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.Synavlia (
    EkdilosiID  INT NOT NULL,
    EventType   AS (CAST('S' AS CHAR(1))) PERSISTED,
    Titlos      NVARCHAR(200) NOT NULL,        -- τίτλος/ονομασία συναυλίας
    Xoros       NVARCHAR(200) NULL,             -- χώρος διεξαγωγής
    CONSTRAINT PK_Synavlia PRIMARY KEY (EkdilosiID),
    CONSTRAINT FK_Synavlia_Ekdilosi FOREIGN KEY (EkdilosiID, EventType)
        REFERENCES dbo.Ekdilosi (EkdilosiID, EventType)
);
GO

/* ---------------------------------------------------------------------
   SymmetoxesEkdilosis (Παρουσίες ατόμων σε πρόβες/συναυλίες)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.SymmetoxesEkdilosis (
    SymmetoxiID INT IDENTITY(1,1) NOT NULL,
    EkdilosiID  INT               NOT NULL,
    AtomoID     INT               NOT NULL,
    Parousia    BIT               NOT NULL DEFAULT (1),  -- παρών/απών
    ExtraInfo   NVARCHAR(200)     NULL,
    CONSTRAINT PK_SymmetoxesEkdilosis PRIMARY KEY (SymmetoxiID),
    CONSTRAINT FK_SymmetoxesEkdilosis_Ekdilosi FOREIGN KEY (EkdilosiID)
        REFERENCES dbo.Ekdilosi (EkdilosiID),
    CONSTRAINT FK_SymmetoxesEkdilosis_Atomo FOREIGN KEY (AtomoID)
        REFERENCES dbo.Atomo (AtomoID),
    CONSTRAINT UQ_SymmetoxesEkdilosis UNIQUE (EkdilosiID, AtomoID)
);
GO

/* ---------------------------------------------------------------------
   Synthetis (Συνθέτης) / Stixourgos (Στιχουργός)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.Synthetis (
    SynthetisID         INT IDENTITY(1,1) NOT NULL,
    SynthetisEponymo    NVARCHAR(100)     NOT NULL,
    SynthetisOnoma      NVARCHAR(100)     NULL,
    CONSTRAINT PK_Synthetis PRIMARY KEY (SynthetisID)
);
GO

CREATE TABLE dbo.Stixourgos (
    StixourgosID        INT IDENTITY(1,1) NOT NULL,
    StixourgosEponymo   NVARCHAR(100)     NOT NULL,
    StixourgosOnoma     NVARCHAR(100)     NULL,
    CONSTRAINT PK_Stixourgos PRIMARY KEY (StixourgosID)
);
GO

/* ---------------------------------------------------------------------
   Kommati (Μουσικό κομμάτι)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.Kommati (
    KommatiID   INT IDENTITY(1,1) NOT NULL,
    Titlos      NVARCHAR(200)     NOT NULL,
    Xronia      INT               NULL,        -- έτος σύνθεσης/έκδοσης
    ExtraInfo   NVARCHAR(1000)    NULL,
    CONSTRAINT PK_Kommati PRIMARY KEY (KommatiID)
);
GO

/* Kommati <-> Synthetis (πολλά-προς-πολλά) */
CREATE TABLE dbo.KommatiaSynthetes (
    KommatiID   INT NOT NULL,
    SynthetisID INT NOT NULL,
    CONSTRAINT PK_KommatiaSynthetes PRIMARY KEY (KommatiID, SynthetisID),
    CONSTRAINT FK_KommatiaSynthetes_Kommati FOREIGN KEY (KommatiID)
        REFERENCES dbo.Kommati (KommatiID),
    CONSTRAINT FK_KommatiaSynthetes_Synthetis FOREIGN KEY (SynthetisID)
        REFERENCES dbo.Synthetis (SynthetisID)
);
GO

/* Kommati <-> Stixourgos (πολλά-προς-πολλά) */
CREATE TABLE dbo.KommatiaStixourgoi (
    KommatiID     INT NOT NULL,
    StixourgosID  INT NOT NULL,
    CONSTRAINT PK_KommatiaStixourgoi PRIMARY KEY (KommatiID, StixourgosID),
    CONSTRAINT FK_KommatiaStixourgoi_Kommati FOREIGN KEY (KommatiID)
        REFERENCES dbo.Kommati (KommatiID),
    CONSTRAINT FK_KommatiaStixourgoi_Stixourgos FOREIGN KEY (StixourgosID)
        REFERENCES dbo.Stixourgos (StixourgosID)
);
GO

/* ---------------------------------------------------------------------
   KommatiaEkdilosis (Ρεπερτόριο ανά πρόβα/συναυλία)
   --------------------------------------------------------------------- */
CREATE TABLE dbo.KommatiaEkdilosis (
    KommatiEkdilosiID  INT IDENTITY(1,1) NOT NULL,
    EkdilosiID         INT           NOT NULL,
    KommatiID          INT           NOT NULL,
    ExtraInfo          NVARCHAR(200) NULL,
    CONSTRAINT PK_KommatiaEkdilosis PRIMARY KEY (KommatiEkdilosiID),
    CONSTRAINT FK_KommatiaEkdilosis_Ekdilosi FOREIGN KEY (EkdilosiID)
        REFERENCES dbo.Ekdilosi (EkdilosiID),
    CONSTRAINT FK_KommatiaEkdilosis_Kommati FOREIGN KEY (KommatiID)
        REFERENCES dbo.Kommati (KommatiID),
    CONSTRAINT UQ_KommatiaEkdilosis UNIQUE (EkdilosiID, KommatiID)
);
GO

/* =====================================================================
   Seed data
   ===================================================================== */

INSERT INTO dbo.Foni (FoniSynt, FoniDescr) VALUES
    (N'S',   N'Soprano'),
    (N'A',   N'Alto'),
    (N'BAL', N'Baladeur');
GO
