# Hard-link xLODGen's finished terrain output into Data, as lod.ps1's terrain step does after its finish check
# (round 5 close-8, 2026-11-03: the output was complete, 14545 files, but the driver's read of the tool's window failed).
$Data = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'; $src = 'C:\argonia\lod\out\terrain'
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class HL2 {
  [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  public static extern bool CreateHardLink(string link, string target, IntPtr sa); }' -EA SilentlyContinue
$n = 0
foreach ($f in [IO.Directory]::EnumerateFiles($src, '*', 'AllDirectories')) {
  $dst = "\\?\$Data" + $f.Substring($src.Length)
  [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))
  if ([IO.File]::Exists($dst)) { [IO.File]::Delete($dst) }
  if (-not [HL2]::CreateHardLink($dst, "\\?\$f", [IntPtr]::Zero)) { throw "link failed: $f" }
  $n++
}
"linked $n files from $src into Data"
