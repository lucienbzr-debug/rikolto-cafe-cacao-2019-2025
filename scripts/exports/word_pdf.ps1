param([string]$Path, [string]$Pdf)
$w = New-Object -ComObject Word.Application; $w.Visible=$false; $w.DisplayAlerts=0
try { $d = $w.Documents.Open($Path, $false, $true); "pages=" + $d.ComputeStatistics(2); $d.ExportAsFixedFormat($Pdf, 17); $d.Close($false) }
finally { $w.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($w) }
