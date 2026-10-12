/* =====================================================================
   Migration 003: προσθήκη Atomo.ImerominiaEggrafis / ImerominiaApoxorisis
   (μη destructive, επαναλήψιμο).

   Χορωδός χωρίς ημερομηνία αποχώρησης θεωρείται ενεργός. Οι υπάρχοντες
   χορωδοί μένουν με NULL και στις δύο ημερομηνίες (άρα ενεργοί).
   ===================================================================== */

USE ChoirApp;
GO

IF COL_LENGTH('dbo.Atomo', 'ImerominiaEggrafis') IS NULL
    ALTER TABLE dbo.Atomo ADD ImerominiaEggrafis DATE NULL;
GO

IF COL_LENGTH('dbo.Atomo', 'ImerominiaApoxorisis') IS NULL
    ALTER TABLE dbo.Atomo ADD ImerominiaApoxorisis DATE NULL;
GO
