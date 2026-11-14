# Installs the Windows SDK that ANGLE's build pins (the runner image has a different one).
param([string]$Source)
$ErrorActionPreference = 'Stop'
$text = Get-Content "$Source\build\toolchain\win\setup_toolchain.py" -Raw
if ($text -notmatch "(?m)^SDK_VERSION\s*=\s*'([0-9.]+)'") { throw 'SDK_VERSION not found' }
$want = $Matches[1]
$sdk = "C:\Program Files (x86)\Windows Kits\10"
if (Test-Path "$sdk\Include\$want\um\Windows.h") { "SDK $want already installed"; exit 0 }
$prefix = ($want -split '\.')[0..2] -join '.'
$page = (Invoke-WebRequest 'https://learn.microsoft.com/en-us/windows/apps/windows-sdk/downloads?accept=text/markdown' -Headers @{Accept='text/markdown'}).Content
$rows = [regex]::Matches($page, 'Windows SDK for Windows[^\r\n]*\((' + [regex]::Escape($prefix) + '\.(\d+))\)[^\r\n]*?\[Installer\]\((https://go\.microsoft\.com/fwlink/\?linkid=\d+)\)')
if ($rows.Count -eq 0) { throw "no installer listed for $prefix" }
$best = $rows | Sort-Object { [int]$_.Groups[2].Value } -Descending | Select-Object -First 1
"Installing SDK $($best.Groups[1].Value) for pinned $want"
$exe = Join-Path $env:RUNNER_TEMP 'winsdksetup.exe'
Invoke-WebRequest $best.Groups[3].Value -OutFile $exe
$sig = Get-AuthenticodeSignature $exe
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') { throw "bad signature: $($sig.Status) $($sig.SignerCertificate.Subject)" }
$p = Start-Process $exe -Wait -PassThru -ArgumentList '/features','OptionId.DesktopCPPx64','OptionId.WindowsDesktopDebuggers','/quiet','/norestart','/ceip','off'
if ($p.ExitCode -notin 0, 3010) { throw "SDK installer exit code $($p.ExitCode)" }
if (-not (Test-Path "$sdk\Include\$want\um\Windows.h")) { throw "SDK $want still missing after install" }
"SDK $want installed"
