<#
.SYNOPSIS
    One-shot setup for the Enron ILI pipeline on Windows, including machines
    with no working Python at all.

.DESCRIPTION
    scripts\bootstrap-v2.py does the real work, but it is a Python script, so it
    needs *a* Python to start. On a fresh Windows machine there often isn't one:

      * the `py` launcher is only installed by python.org installers, not by
        the Microsoft Store package, so `py` frequently does not exist; and
      * `python.exe` on PATH is usually the Microsoft Store "App Execution
        Alias" stub in %LOCALAPPDATA%\Microsoft\WindowsApps, which is not a
        Python at all -- running it opens the Store.

    This script removes that chicken-and-egg problem. uv is a single native
    binary with no Python dependency, so it can be installed first and then
    used to install a real CPython 3.14.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1 --diagnose-only
#>
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $Forward)

$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSCommandPath)

function Find-Uv {
    foreach ($c in @(
        (Get-Command uv -ErrorAction SilentlyContinue | Select-Object -Expand Source),
        "$env:USERPROFILE\.local\bin\uv.exe",
        "$env:USERPROFILE\.cargo\bin\uv.exe"
    )) { if ($c -and (Test-Path $c)) { return $c } }
    return $null
}

Write-Host "=== Enron ILI pipeline: Windows bootstrap ===`n"

$uv = Find-Uv
if ($uv) {
    Write-Host "[skip] uv already installed: $uv"
} else {
    Write-Host "[..] installing uv (one user-local binary, no admin rights needed)"
    # Make uv use the Windows certificate store, which is what lets it work
    # behind a corporate proxy doing TLS inspection. Older uv spells this
    # UV_NATIVE_TLS; that name is deprecated and warns on current versions.
    $env:UV_SYSTEM_CERTS = '1'
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $uv = Find-Uv
    if (-not $uv) {
        Write-Error @"
Could not install uv.

If this machine is behind a corporate proxy, ask IT for the proxy root CA and
set SSL_CERT_FILE to it, then re-run. Otherwise download uv manually from
https://github.com/astral-sh/uv/releases (uv-x86_64-pc-windows-msvc.zip),
put uv.exe in %USERPROFILE%\.local\bin, and re-run this script.
"@
        exit 1
    }
    Write-Host "[ok] uv installed: $uv"
}

Write-Host "[..] installing CPython 3.14 via uv"
& $uv python install 3.14
if ($LASTEXITCODE -ne 0) { Write-Error "uv could not install Python 3.14."; exit 1 }
Write-Host "[ok] Python 3.14 available to uv`n"

# --no-project: bootstrap-v2.py is stdlib-only and must NOT get the project
# environment, which it is about to create itself.
Write-Host "[..] handing over to scripts\bootstrap-v2.py`n"
& $uv run --no-project --python 3.14 "$root\scripts\bootstrap-v2.py" @Forward
exit $LASTEXITCODE
