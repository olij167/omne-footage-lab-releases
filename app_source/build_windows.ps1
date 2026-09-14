$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = (Get-Command python.exe -ErrorAction Stop).Source
$Version = (& $Python -c 'import ast,pathlib; t=ast.parse(pathlib.Path("omne_footage_lab.py").read_text(encoding="utf-8")); print(next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="VERSION" for x in n.targets)))')
$Arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
if ($Arch -notin @("X64", "Arm64")) { throw "Unsupported Windows build architecture: $Arch" }
$ArchLabel = if ($Arch -eq "Arm64") { "arm64" } else { "x64" }
$AppName = "OmN-e Retrospector"

$Ffmpeg = (Get-Command ffmpeg.exe -ErrorAction Stop).Source
$Ffprobe = (Get-Command ffprobe.exe -ErrorAction Stop).Source

& $Python -m pip install --upgrade pip
& $Python -m pip install 'pyinstaller>=6.22,<7' 'pillow>=11,<13'
if ($LASTEXITCODE -ne 0) { throw "Build dependencies failed" }

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist, dist-installer

& $Python -m PyInstaller --noconfirm --clean --windowed --name $AppName `
  --hidden-import=PIL._tkinter_finder `
  --add-binary "$Ffmpeg;tools" --add-binary "$Ffprobe;tools" `
  --add-data ".\ui_profile.json;." .\omne_footage_lab.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

$Dist = Join-Path $Root "dist\$AppName"
if (-not (Test-Path $Dist)) { throw "PyInstaller output folder missing: $Dist" }

foreach ($f in @("README.txt","QA_REPORT.txt","RELEASE_GUIDE.md","SYSTEM_REQUIREMENTS.md","THIRD_PARTY_NOTICES.txt")) {
  if (Test-Path $f) { Copy-Item $f $Dist -Force }
}

$Zip = Join-Path $Root "OmN-e_Retrospector_v${Version}_Windows_${ArchLabel}_Portable.zip"
Compress-Archive -Path "$Dist\*" -DestinationPath $Zip -CompressionLevel Optimal -Force
(Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLower() + "  " + (Split-Path -Leaf $Zip) | Set-Content -Encoding ascii "${Zip}.sha256"
Write-Host "Windows portable ZIP: $Zip"

$IsccCandidates = @(
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "$env:ChocolateyInstall\bin\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $Iscc) {
  $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($cmd) { $Iscc = $cmd.Source }
}
if (-not $Iscc) {
  throw "Inno Setup 6 was not found. Install it before building the public Windows installer."
}

# The public updater uses the x64 setup today. Arm64 builds are allowed for
# local/CI evaluation, but use their own filename and never overwrite x64.
& $Iscc "/DMyAppVersion=$Version" "/DMyAppArch=$ArchLabel" .\windows_installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }

$Setup = Join-Path $Root "dist-installer\OmN-e_Retrospector_v${Version}_Windows_${ArchLabel}_Setup.exe"
if (-not (Test-Path $Setup)) { throw "Installer output missing: $Setup" }

# Optional Authenticode signing. The certificate should already be available
# to the current account (CI may import a temporary PFX before this script).
$SignTool = Get-Command signtool.exe -ErrorAction SilentlyContinue
$Thumbprint = $env:OMNE_WINDOWS_CERT_THUMBPRINT
if ($SignTool -and $Thumbprint) {
  & $SignTool.Source sign /sha1 $Thumbprint /fd SHA256 /td SHA256 /tr "http://timestamp.digicert.com" $Setup
  if ($LASTEXITCODE -ne 0) { throw "Authenticode signing failed" }
}

(Get-FileHash -Algorithm SHA256 $Setup).Hash.ToLower() + "  " + (Split-Path -Leaf $Setup) | Set-Content -Encoding ascii "${Setup}.sha256"
Write-Host "Windows installer: $Setup"
if (-not $Thumbprint) { Write-Host "NOTE: unsigned Windows test build. Code signing is recommended for public distribution." }
