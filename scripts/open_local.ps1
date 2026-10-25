$ErrorActionPreference = 'Stop'
$siteRoot = Split-Path $PSScriptRoot -Parent
$port = 4173
$url = "http://127.0.0.1:$port/"
$manifestUrl = "http://127.0.0.1:$port/data/manifest.json"

function Test-PracticeServer {
    try {
        $manifest = Invoke-RestMethod -Uri $manifestUrl -TimeoutSec 2
        return $manifest.total -eq 10000
    } catch {
        return $false
    }
}

if (-not (Test-PracticeServer)) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        throw "端口 $port 已被其他程序占用。请关闭占用程序后重试。"
    }
    $python = Get-Command python -ErrorAction Stop
    Start-Process -FilePath $python.Source -ArgumentList @('-m', 'http.server', "$port", '--directory', 'dist') -WorkingDirectory $siteRoot -WindowStyle Hidden
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-PracticeServer) { $ready = $true; break }
    }
    if (-not $ready) { throw '练习站未能启动，请确认 Python 已安装。' }
}
Start-Process $url
