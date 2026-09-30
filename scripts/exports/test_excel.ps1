param([string]$Path, [string]$Pdf)
$x = New-Object -ComObject Excel.Application; $x.Visible=$false; $x.DisplayAlerts=$false
try {
 $wb = $x.Workbooks.Open($Path, 0, $true)
 $d = $wb.Worksheets.Item("Dashboard")
 $d.Range("C4").Value2 = "2025"; $d.Range("C5").Value2 = "CKK"; $x.CalculateFull()
 "filtre 2025/CKK: " + ((2..7 | ForEach-Object { $d.Cells.Item(9,$_).Text }) -join " | ")
 "series CKK 2019: " + ((2..6 | ForEach-Object { $wb.Worksheets.Item(3).Cells.Item(7,$_).Text }) -join " | ")
 $d.Range("C4").Value2 = "Toutes"; $d.Range("C5").Value2 = "Toutes"; $x.CalculateFull()
 $d.PageSetup.Orientation = 1; $d.PageSetup.Zoom = $false; $d.PageSetup.FitToPagesWide = 1; $d.PageSetup.FitToPagesTall = $false
 $d.ExportAsFixedFormat(0, $Pdf)
 $wb.Close($false)
} finally { $x.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($x) }
