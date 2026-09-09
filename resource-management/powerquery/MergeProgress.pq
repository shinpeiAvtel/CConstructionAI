let
    FolderPath = "C:\\ResourceManagement\\EmployeeFiles",
    Source = Folder.Files(FolderPath),
    VisibleFiles = Table.SelectRows(Source, each [Attributes]?[Hidden]? <> true),
    ExcelFiles = Table.SelectRows(VisibleFiles, each let ext = Text.Lower([Extension]) in ext = ".xlsx" or ext = ".xlsm"),
    EmployeeFiles = Table.SelectRows(ExcelFiles, each [Name] <> "General_Resource_Management.xlsx"),
    ProgressTables = Table.AddColumn(
        EmployeeFiles,
        "ProgressTable",
        each Table.SelectRows(Excel.Workbook([Content], true), each [Kind] = "Table" and [Item] = "tblProgressUpdate")
    ),
    ExpandedProgressTables = Table.ExpandTableColumn(ProgressTables, "ProgressTable", {"Data"}, {"Data"}),
    ExpandedRows = Table.ExpandTableColumn(
        ExpandedProgressTables,
        "Data",
        {"progress_entry_id", "employee_id", "project_id", "progress_date", "progress_percent", "actual_hours", "progress_status", "issue_flag", "update_comment"},
        {"progress_entry_id", "employee_id", "project_id", "progress_date", "progress_percent", "actual_hours", "progress_status", "issue_flag", "update_comment"}
    ),
    AddedSourceFile = Table.AddColumn(ExpandedRows, "source_file", each [Name], type text),
    AddedRefreshTime = Table.AddColumn(AddedSourceFile, "last_refresh_at", each DateTime.LocalNow(), type datetime),
    SelectedColumns = Table.SelectColumns(
        AddedRefreshTime,
        {"progress_entry_id", "employee_id", "project_id", "progress_date", "progress_percent", "actual_hours", "progress_status", "issue_flag", "update_comment", "source_file", "last_refresh_at"}
    )
in
    SelectedColumns
