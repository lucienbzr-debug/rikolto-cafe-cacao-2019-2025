param([string]$Path, [string]$Pdf)
$p = New-Object -ComObject PowerPoint.Application
try { $d = $p.Presentations.Open($Path, $true, $false, $false); "slides=" + $d.Slides.Count; $d.SaveAs($Pdf, 32); $d.Close() }
finally { $p.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($p) }
