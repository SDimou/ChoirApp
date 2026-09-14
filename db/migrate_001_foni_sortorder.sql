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
WHERE FoniSynt IN (N'S', N'BAL', N'A') AND SortOrder = 0;
GO
