let
    FolderPath = "C:\\ResourceManagement\\EmployeeFiles",
    Source = Folder.Files(FolderPath),
    VisibleFiles = Table.SelectRows(Source, each [Attributes]?[Hidden]? <> true),
    ExcelFiles = Table.SelectRows(VisibleFiles, each let ext = Text.Lower([Extension]) in ext = ".xlsx" or ext = ".xlsm"),
    EmployeeFiles = Table.SelectRows(ExcelFiles, each [Name] <> "General_Resource_Management.xlsx"),
    ScheduleTables = Table.AddColumn(
        EmployeeFiles,
        "ScheduleTable",
        each Table.SelectRows(Excel.Workbook([Content], true), each [Kind] = "Table" and [Item] = "tblPersonalSchedule")
    ),
    ExpandedScheduleTables = Table.ExpandTableColumn(ScheduleTables, "ScheduleTable", {"Data"}, {"Data"}),
    ExpandedRows = Table.ExpandTableColumn(
        ExpandedScheduleTables,
        "Data",
        {"entry_id", "employee_id", "work_date", "project_id", "task_name", "planned_hours", "availability_status", "remarks"},
        {"entry_id", "employee_id", "work_date", "project_id", "task_name", "planned_hours", "availability_status", "remarks"}
    ),
    AddedSourceFile = Table.AddColumn(ExpandedRows, "source_file", each [Name], type text),
    AddedRefreshTime = Table.AddColumn(AddedSourceFile, "last_refresh_at", each DateTime.LocalNow(), type datetime),
    SelectedColumns = Table.SelectColumns(
        AddedRefreshTime,
        {"entry_id", "employee_id", "work_date", "project_id", "task_name", "planned_hours", "availability_status", "remarks", "source_file", "last_refresh_at"}
    )
in
    SelectedColumns
