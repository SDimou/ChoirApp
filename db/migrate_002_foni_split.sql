/* =====================================================================
   Migration 002: διαχωρισμός Σοπράνο -> Σοπράνο 1/2 και Άλτο -> Άλτο 1/2
   (μη destructive, επαναλήψιμο).

   Οι υπάρχουσες εγγραφές S και A μετονομάζονται σε S1 και A1 (κρατούν
   το FoniID, άρα τα μέλη που τις χρησιμοποιούν παραμένουν ως έχουν) και
   προστίθενται οι S2 και A2. Το SortOrder ξαναορίζεται:
   S1=1, S2=2, BAL=3, A1=4, A2=5.
   ===================================================================== */

USE ChoirApp;
GO

UPDATE dbo.Foni SET FoniSynt = N'S1', FoniDescr = N'Soprano 1' WHERE FoniSynt = N'S';
UPDATE dbo.Foni SET FoniSynt = N'A1', FoniDescr = N'Alto 1'    WHERE FoniSynt = N'A';

INSERT INTO dbo.Foni (FoniSynt, FoniDescr, SortOrder)
SELECT v.Synt, v.Descr, 0
FROM (VALUES (N'S2', N'Soprano 2'), (N'A2', N'Alto 2')) AS v(Synt, Descr)
WHERE NOT EXISTS (SELECT 1 FROM dbo.Foni f WHERE f.FoniSynt = v.Synt);

UPDATE dbo.Foni
SET SortOrder = CASE FoniSynt
    WHEN N'S1'  THEN 1
    WHEN N'S2'  THEN 2
    WHEN N'BAL' THEN 3
    WHEN N'A1'  THEN 4
    WHEN N'A2'  THEN 5
END
WHERE FoniSynt IN (N'S1', N'S2', N'BAL', N'A1', N'A2');
GO
