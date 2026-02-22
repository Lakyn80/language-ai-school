param(
    [switch]$NoCache,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $repoRoot

try {
    if (-not $SkipTests) {
        Write-Host "Running backend tests..."
        python -m pytest -q backend
        if ($LASTEXITCODE -ne 0) {
            throw "Tests failed. Deployment stopped."
        }
    }

    Write-Host "Building Docker images..."
    if ($NoCache) {
        docker compose build --no-cache
    } else {
        docker compose build
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed."
    }

    Write-Host "Starting Docker services..."
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "Docker start failed."
    }

    $healthUrl = "http://localhost:8086/api/health/"
    $deadline = (Get-Date).AddSeconds(90)
    $healthy = $false

    Write-Host "Waiting for backend health check..."
    while ((Get-Date) -lt $deadline) {
        $status = & curl.exe -s -o NUL -w "%{http_code}" $healthUrl
        if ($status -eq "200") {
            $healthy = $true
            break
        }
        Start-Sleep -Seconds 2
    }

    if (-not $healthy) {
        Write-Host "Backend did not become healthy. Recent logs:"
        docker logs --tail 120 language-ai-backend
        throw "Health check failed: $healthUrl"
    }

    Write-Host "Done. Backend is healthy at $healthUrl"
}
finally {
    Pop-Location
}
