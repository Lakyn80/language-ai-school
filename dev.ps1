$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$tag = "dev-$timestamp"

Write-Host "----------------------------------------"
Write-Host " Building Language AI School"
Write-Host " TAG: $tag"
Write-Host "----------------------------------------"

$env:TAG = $tag

docker compose down

docker compose build --no-cache

docker compose up -d

Write-Host ""
Write-Host "Backend running:"
Write-Host "http://localhost:8086/api/health"
Write-Host ""
