#requires -version 5.1
<#
 PulseRing Super V2.8.1 APK source recovery
 Only recover your own project. This script NEVER pushes to GitHub.
 Obtains JADX from its official GitHub release (network required).
 Decompiled code is approximate Java, NOT the original Kotlin source.
#>
[CmdletBinding()]
param([string]$ApkPath = (Join-Path $PSScriptRoot 'PRIVATE_INPUT\PulseRing Super V2.8.1.apk'))
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$ApkPath = (Resolve-Path -LiteralPath $ApkPath).Path
$jadxVersion = '1.5.6'
$tools = Join-Path $root 'LOCAL_TOOLS'
$work = Join-Path $root 'WORK_DECOMPILED_NOT_FOR_GITHUB'
$public = Join-Path $root 'GITHUB_REVIEW_BEFORE_PUSH'
$zip = Join-Path $tools 'jadx-1.5.6.zip'
$jadxDir = Join-Path $tools 'jadx'
$exe = Join-Path $jadxDir 'bin\jadx.bat'
New-Item -ItemType Directory -Force -Path $tools | Out-Null
if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    throw 'Java 11+ not detected. Install a supported JDK, reopen PowerShell, then rerun this script.'
}
if (-not (Test-Path -LiteralPath $exe)) {
    if (-not (Test-Path -LiteralPath $zip)) {
        $url = 'https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip'
        Write-Host "Downloading JADX $jadxVersion from official releases..."
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    }
    Expand-Archive -LiteralPath $zip -DestinationPath $jadxDir -Force
}
if (Test-Path -LiteralPath $work) { throw "Existing output at $work. Move it away if you want a fresh decompile (no automatic deletion)." }
Write-Host 'Decompiling APK (this can produce thousands of files)...'
& $exe --threads-count 4 -d $work $ApkPath
if ($LASTEXITCODE -ne 0) { throw "JADX returned exit code $LASTEXITCODE. Inspect errors and output folder before proceeding." }
# Only the application's own package is staged. Do not publish the 3rd party decompiled classes.
$src = Join-Path $work 'sources\com\conner\fixfate'
if (-not (Test-Path -LiteralPath $src)) { throw "Application source folder missing: $src" }
if (Test-Path -LiteralPath $public) { throw "Existing public review folder at $public; move aside to avoid mixing old files." }
$dstParent = Join-Path $public 'app\src\main\java\com\conner'
New-Item -ItemType Directory -Force -Path $dstParent | Out-Null
Copy-Item -LiteralPath $src -Destination (Join-Path $dstParent 'fixfate') -Recurse -Force
# Decompiled resources are copied for manual review. Do not infer they are the original Android Studio source files.
$resSrc = Join-Path $work 'resources'
$resDest = Join-Path $public 'DECOMPILED_RESOURCES_REVIEW'
if (Test-Path -LiteralPath $resSrc) { Copy-Item -LiteralPath $resSrc -Destination $resDest -Recurse -Force }
$notes = @'
# PulseRing Super V2.8.1 - decompiled output / 反編譯結果

This folder contains recovered, **approximate Java** code from an APK originally built from Kotlin.
It is NOT verified as a functioning Android Studio source project, and may require manual reconstruction.

此資料夾包含從 APK 逆向還原的**近似 Java 程式碼**，不等同原始 Kotlin 原始碼，且尚未證實能直接編譯。

* Only `com.conner.fixfate` application classes were copied to the source directory.
* Generated synthetic classes may appear and Kotlin idioms may be distorted.
* External AndroidX / Kotlin / Google libraries must be declared as dependencies, not republished as original source.
* Review `DECOMPILED_RESOURCES_REVIEW` before moving resources to a buildable app tree.
* Establish Android Gradle Plugin, compile SDK, dependency versions, manifest, resources and signing before building.
* Do NOT publish credentials, BLE MACs, personal readings, diagnostic logs, private conversations, user data, or third-party voice samples.
* No automated GitHub push is performed. Inspect all files and choose a license only for material you own.
'@
Set-Content -LiteralPath (Join-Path $public 'README.md') -Value $notes -Encoding UTF8
$ignore = @'
# Never publish local privacy or build artifacts
.env
.env.*
!.env.example
*.jks
*.keystore
*.key
*.pem
*.apk
*.aab
*.log
local.properties
.gradle/
.idea/
.vs/
build/
**/build/
PRIVATE_INPUT/
LOCAL_TOOLS/
WORK_DECOMPILED_NOT_FOR_GITHUB/
'@
Set-Content -LiteralPath (Join-Path $public '.gitignore') -Value $ignore -Encoding UTF8
# Scan high-confidence patterns and print only affected filenames, NEVER secret text.
$patterns = @('sk-proj-[A-Za-z0-9_-]{12,}', 'sk-[A-Za-z0-9_-]{28,}', 'AIza[A-Za-z0-9_-]{30,}', 'ghp_[A-Za-z0-9]{24,}', 'github_pat_[A-Za-z0-9_]{24,}', '(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[=:]\s*["'']?[a-z0-9_-]{18,}')
$hits = @()
Get-ChildItem -LiteralPath $public -File -Recurse | Where-Object { $_.Extension -in @('.java','.xml','.kt','.json','.properties','.txt','.md') } | ForEach-Object {
    $f = $_
    foreach ($p in $patterns) {
        $m = Select-String -LiteralPath $f.FullName -Pattern $p -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($m) { $hits += ($f.FullName.Replace($public,'') + ' : line ' + $m.LineNumber); break }
    }
}
if ($hits.Count -gt 0) {
    Write-Warning 'Potential secrets detected (content redacted). DO NOT PUSH.'
    $hits | Sort-Object -Unique | ForEach-Object { Write-Warning $_ }
    throw 'Potential secrets found. Remove them and any corresponding Git history before publishing.'
}
Write-Host 'Completed local decompilation. IMPORTANT: Manual privacy, license, and build review still required.'
Write-Host "Review output: $public"
Write-Host "Unfiltered output (PRIVATE): $work"
