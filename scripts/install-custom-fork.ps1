$ErrorActionPreference = 'Stop'

Write-Host 'Open WebUI Custom Fork v1 installer' -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker was not found. Install Docker Desktop, start it, then run this script again.'
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker is installed but is not running. Start Docker Desktop and try again.'
}

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env from .env.example.' -ForegroundColor Green
}

$composeArgs = @('compose')
if ($env:OPEN_WEBUI_GPU -eq 'nvidia') {
    $composeArgs += @('-f', 'docker-compose.yaml', '-f', 'docker-compose.gpu.yaml')
} elseif ($env:OPEN_WEBUI_GPU -eq 'amd') {
    $composeArgs += @('-f', 'docker-compose.yaml', '-f', 'docker-compose.amdgpu.yaml')
}
$composeArgs += @('up', '-d', '--build')

Write-Host 'Building and starting Open WebUI, Ollama and LibreTranslate...'
& docker @composeArgs
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Compose failed. Run docker compose logs for details.'
}

Write-Host ''
Write-Host 'Installation complete.' -ForegroundColor Green
Write-Host 'Open WebUI:       http://localhost:3000'
Write-Host 'LibreTranslate:   http://127.0.0.1:5000'
Write-Host ''
Write-Host 'Optional GPU selection before running:'
Write-Host '  $env:OPEN_WEBUI_GPU="nvidia"'
Write-Host '  $env:OPEN_WEBUI_GPU="amd"'
