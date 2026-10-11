param([switch]$VideoOnly)
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $workspace
$python = Join-Path $workspace '.venv/Scripts/python.exe'
$client = Join-Path $workspace 'runtime/foxglove/Foxglove.exe'
if (-not (Test-Path $python)) { throw 'Create the Python environment as described in tools/pc/README.md.' }
if (-not (Test-Path $client)) { throw 'Foxglove is expected at runtime/foxglove/Foxglove.exe.' }
$arguments = @('tools/pc/camera_analysis.py')
if ($VideoOnly) { $arguments += '--video-only' }
$videoTunnel = Get-NetTCPConnection -LocalPort 8554 -State Listen -ErrorAction SilentlyContinue
if (-not $videoTunnel) {
    $sshConfig = Join-Path $workspace 'pi.sshconfig.local'
    $sshArguments = @('-F', ('"' + $sshConfig + '"'), '-N', '-L', '127.0.0.1:8554:127.0.0.1:8554', '-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', 'rover-pi')
    Start-Process -FilePath 'ssh.exe' -ArgumentList $sshArguments -WindowStyle Hidden
    Start-Sleep -Seconds 2
}
$listener = Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
    $runtime = Join-Path $workspace 'runtime'
    New-Item -ItemType Directory -Force $runtime | Out-Null
    $process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $workspace -WindowStyle Hidden -PassThru -RedirectStandardOutput "$runtime/vision.stdout.log" -RedirectStandardError "$runtime/vision.stderr.log"
    $process.Id | Set-Content "$runtime/vision.pid"
    Start-Sleep -Seconds 2
    if ($process.HasExited) { throw "Vision process exited; see $runtime/vision.stderr.log." }
}
$electronNodeMode = $env:ELECTRON_RUN_AS_NODE
try {
    Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
    Start-Process -FilePath $client -ArgumentList 'foxglove://open?ds=foxglove-websocket&ds.url=ws%3A%2F%2F127.0.0.1%3A8766'
} finally {
    if ($null -ne $electronNodeMode) { $env:ELECTRON_RUN_AS_NODE = $electronNodeMode }
}
Write-Output 'Foxglove opened. Import tools/pc/foxglove-layout.json from Layouts > Import from file.'
