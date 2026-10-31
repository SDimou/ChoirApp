/* =====================================================================
   Migration 005: soft delete σε Ekdilosi, Atomo, Kommati
   (μη destructive, επαναλήψιμο).

   IsDeleted = 1 σημαίνει ότι η εγγραφή έχει σβηστεί και εμφανίζεται μόνο
   στη σελίδα "Σβησμένες Εγγραφές". Οι υπάρχουσες εγγραφές μένουν με 0.
   ===================================================================== */

USE ChoirApp;
GO

IF COL_LENGTH('dbo.Ekdilosi', 'IsDeleted') IS NULL
    ALTER TABLE dbo.Ekdilosi ADD IsDeleted BIT NOT NULL CONSTRAINT DF_Ekdilosi_IsDeleted DEFAULT (0);
GO

IF COL_LENGTH('dbo.Atomo', 'IsDeleted') IS NULL
    ALTER TABLE dbo.Atomo ADD IsDeleted BIT NOT NULL CONSTRAINT DF_Atomo_IsDeleted DEFAULT (0);
GO

IF COL_LENGTH('dbo.Kommati', 'IsDeleted') IS NULL
    ALTER TABLE dbo.Kommati ADD IsDeleted BIT NOT NULL CONSTRAINT DF_Kommati_IsDeleted DEFAULT (0);
GO
