/* =====================================================================
   Παραχώρηση πρόσβασης σε επιπλέον χρήστες Windows στη βάση ChoirApp.

   Η εφαρμογή συνδέεται με Trusted Connection (Windows Authentication).
   Το να έχει κάποιος ήδη login στο SQL Server instance δεν αρκεί — πρέπει
   να έχει και database user στο ChoirApp με τους κατάλληλους ρόλους.

   Τρέξε αυτό το script (πάνω στο ChoirApp) για κάθε επιπλέον Windows
   λογαριασμό που πρέπει να έχει πρόσβαση στην εφαρμογή. Αν ο server
   login δεν υπάρχει ακόμα, δημιούργησέ τον πρώτα:
       CREATE LOGIN [ΜΗΧΑΝΗΜΑ\χρήστης] FROM WINDOWS;
   ===================================================================== */

USE ChoirApp;
GO

-- Παράδειγμα: SPEEDY\chrys (ίδιο pattern με το MonthlyFood)
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'SPEEDY\chrys')
BEGIN
    CREATE USER [SPEEDY\chrys] FOR LOGIN [SPEEDY\chrys];
    ALTER ROLE db_datareader ADD MEMBER [SPEEDY\chrys];
    ALTER ROLE db_datawriter ADD MEMBER [SPEEDY\chrys];
END
GO
