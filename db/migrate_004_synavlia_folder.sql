/* =====================================================================
   Migration 004: προσθήκη Synavlia.FolderSynavlias (μη destructive,
   επαναλήψιμο). Διαδρομή του φακέλου της συναυλίας (π.χ. Z:\...).
   ===================================================================== */

USE ChoirApp;
GO

IF COL_LENGTH('dbo.Synavlia', 'FolderSynavlias') IS NULL
    ALTER TABLE dbo.Synavlia ADD FolderSynavlias NVARCHAR(500) NULL;
GO
