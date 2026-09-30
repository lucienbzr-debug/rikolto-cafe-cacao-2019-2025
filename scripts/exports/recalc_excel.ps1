param([string]$Path)
$x = New-Object -ComObject Excel.Application
$x.Visible = $false; $x.DisplayAlerts = $false
try {
  $wb = $x.Workbooks.Open($Path)
  $x.CalculateFull()
  $errs = @(); $nf = 0
  foreach ($sh in $wb.Worksheets) {
    $ur = $sh.UsedRange
    foreach ($c in $ur.Cells) {
      if ($c.HasFormula) { $nf++ ; $t = [string]$c.Text; if ($t -match '^#') { $errs += ($sh.Name + '!' + $c.Address(0,0) + ' ' + $t) } }
    }
  }
  $wb.Save(); $wb.Close($true)
  "formulas=$nf errors=$($errs.Count)"; $errs | Select-Object -First 30
} finally { $x.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($x) }
