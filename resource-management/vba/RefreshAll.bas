Attribute VB_Name = "RefreshAll"
Option Explicit

Public Sub Refresh_All_Resource_Management()
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual

    On Error GoTo CleanUp

    ThisWorkbook.RefreshAll
    Application.CalculateUntilAsyncQueriesDone
    Application.CalculateFullRebuild

CleanUp:
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
    Application.ScreenUpdating = True

    If Err.Number <> 0 Then
        MsgBox "Refresh failed: " & Err.Description, vbExclamation, "Resource Management"
    Else
        MsgBox "Resource management workbook refreshed.", vbInformation, "Resource Management"
    End If
End Sub
