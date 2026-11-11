# Static checks of the machine's PowerShell scripts, run on the machine before any long step (lod.sh preflight):
#   PARSE     a parser error
#   SHADOW    a function assigns a name the script scope holds (PowerShell names are case-blind: a local $out hides
#             the script's $Out for the rest of that function)
#   CASE      one name assigned under two spellings anywhere in the file
#   EXITCODE  .ExitCode read from a Start-Process whose handle was never taken ($null = $p.Handle): PowerShell 5.1
#             returns nothing for it once the process has gone
#   PSSA      PSScriptAnalyzer errors (when the module is installed)
# One line per fault; the last line is "pscheck: N faults" and the exit code is 1 when N > 0.
param([Parameter(Mandatory)][string[]]$Files)
$Files = @($Files | % { $_ -split "," } | ? { $_ })  # -File passes a,b as one string
$ErrorActionPreference = 'Stop'
$L = [System.Management.Automation.Language.Parser]
$faults = New-Object System.Collections.Generic.List[string]
foreach ($f in $Files) {
  $name = Split-Path $f -Leaf
  $tok = $null; $err = $null
  $ast = $L::ParseFile($f, [ref]$tok, [ref]$err)
  foreach ($e in $err) { $faults.Add("PARSE ${name}:$($e.Extent.StartLineNumber) $($e.Message)") }
  $top = @{}
  if ($ast.ParamBlock) { foreach ($p in $ast.ParamBlock.Parameters) { $top[$p.Name.VariablePath.UserPath.ToLower()] = $p.Name.VariablePath.UserPath } }
  foreach ($s in $ast.EndBlock.Statements) {
    if ($s -is [System.Management.Automation.Language.AssignmentStatementAst] -and $s.Left -is [System.Management.Automation.Language.VariableExpressionAst]) {
      $top[$s.Left.VariablePath.UserPath.ToLower()] = $s.Left.VariablePath.UserPath } }
  $assigns = { param($a) $a -is [System.Management.Automation.Language.AssignmentStatementAst] }
  $target = { param($a)  # the variable an assignment writes ($x = ..., [type]$x = ...), or nothing ($x.y = ..., $x[0] = ...)
    $l = $a.Left; while ($l -is [System.Management.Automation.Language.ConvertExpressionAst]) { $l = $l.Child }
    if ($l -is [System.Management.Automation.Language.VariableExpressionAst]) { $l } }
  foreach ($fn in $ast.FindAll({ param($a) $a -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
    foreach ($a in $fn.FindAll($assigns, $true)) {
      $v = & $target $a; if (-not $v) { continue }
      $n = $v.VariablePath.UserPath
      if ($v.VariablePath.IsScript -or $v.VariablePath.IsGlobal) { continue }  # written to the outer scope on purpose
      if ($top.ContainsKey($n.ToLower())) {
        $faults.Add("SHADOW ${name}:$($v.Extent.StartLineNumber) function $($fn.Name) assigns `$$n; the script scope holds `$$($top[$n.ToLower()])") } } }
  $all = @($ast.FindAll($assigns, $true) | % { & $target $_ } | ? { $_ })
  foreach ($g in ($all | Group-Object { $_.VariablePath.UserPath.ToLower() })) {
    $sp = @($g.Group | % { $_.VariablePath.UserPath } | Sort-Object -Unique -CaseSensitive)
    if ($sp.Count -gt 1) { $faults.Add("CASE ${name} `$$($sp -join ' / $') (lines $((@($g.Group | % { $_.Extent.StartLineNumber }) | Sort-Object -Unique) -join ', '))") } }
  # .ExitCode: the variable it is read from must have had .Handle read in the same file
  $handles = @($ast.FindAll({ param($a) $a -is [System.Management.Automation.Language.MemberExpressionAst] -and $a.Member.Extent.Text -eq 'Handle' }, $true) | % { $_.Expression.Extent.Text.ToLower() })
  foreach ($m in $ast.FindAll({ param($a) $a -is [System.Management.Automation.Language.MemberExpressionAst] -and $a.Member.Extent.Text -eq 'ExitCode' }, $true)) {
    if ($m.Expression.Extent.Text.ToLower() -notin $handles) { $faults.Add("EXITCODE ${name}:$($m.Extent.StartLineNumber) $($m.Extent.Text) is read but $($m.Expression.Extent.Text).Handle is never taken") } }
  if (Get-Module -ListAvailable PSScriptAnalyzer) {
    foreach ($r in Invoke-ScriptAnalyzer -Path $f -Severity Error) { $faults.Add("PSSA ${name}:$($r.Line) $($r.RuleName): $($r.Message)") } }
}
$faults
"pscheck: $($faults.Count) faults$(if (-not (Get-Module -ListAvailable PSScriptAnalyzer)) { ' (PSScriptAnalyzer not installed)' })"
exit [int]($faults.Count -gt 0)
