param(
    [int]$MaxCases = 5,
    [string]$Model = "llama3.1:8b",
    [string]$Profile = "P0_neutral",
    [string]$Split = "test",
    [string]$QuickUmlsPath = "quickumls"
)

$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot ".venv311\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing .venv311. Run .\setup_metrics.ps1 first."
}

& $python -c "import sys; assert sys.version_info[:2] == (3, 11), sys.version"
$env:ARCHEHR_SPLIT = $Split

$arguments = @(
    "main.py",
    "--max-cases", $MaxCases,
    "--quality-mode", "observe",
    "--processing", "none",
    "--quickumls-path", $QuickUmlsPath,
    "--skip-plot"
)
if ($Model) { $arguments += @("--model", $Model) }
if ($Profile) { $arguments += @("--profile", $Profile) }

& $python @arguments
