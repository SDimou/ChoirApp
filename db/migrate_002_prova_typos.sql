/* =====================================================================
   Migration 002: προσθήκη Prova.TyposProvas (μη destructive).

   Για την ήδη υπάρχουσα (live) βάση — schema.sql κάνει DROP/CREATE και
   δεν μπορεί να ξανατρέξει πάνω σε δεδομένα παραγωγής. Τρέξε αυτό το
   script μία φορά ανά deployment αντ' αυτού.
   ===================================================================== */

USE ChoirApp;
GO

IF COL_LENGTH('dbo.Prova', 'TyposProvas') IS NULL
BEGIN
    ALTER TABLE dbo.Prova ADD TyposProvas NVARCHAR(20) NOT NULL DEFAULT (N'Κανονική');
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_Prova_TyposProvas')
BEGIN
    ALTER TABLE dbo.Prova ADD CONSTRAINT CK_Prova_TyposProvas
        CHECK (TyposProvas IN (N'Κανονική', N'Προγενική', N'Γενική'));
END
GO
