param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("ai", "automation")]
    [string]$AutomationId
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = "D:\每日必看"
$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logPath = Join-Path $logDir "$stamp-$AutomationId.log"
$runner = Join-Path $root "run-codex-automation.py"

try {
    "[$(Get-Date -Format o)] Starting automation $AutomationId" | Out-File -FilePath $logPath -Encoding utf8
    py $runner $AutomationId 2>&1 | Tee-Object -FilePath $logPath -Append
    $exitCode = $LASTEXITCODE
    "[$(Get-Date -Format o)] Exit code: $exitCode" | Out-File -FilePath $logPath -Encoding utf8 -Append
    exit $exitCode
}
catch {
    "[$(Get-Date -Format o)] ERROR: $($_.Exception.Message)" | Out-File -FilePath $logPath -Encoding utf8 -Append
    exit 1
}
