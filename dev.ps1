param(
  [switch]$NoCache
)

Write-Host "----------------------------------------"
Write-Host " Language AI School – Docker DEV"
Write-Host "----------------------------------------"

docker compose down

if ($NoCache) {
    docker compose -f docker-compose.dev.yml build --no-cache
} else {
    docker compose -f docker-compose.dev.yml build
}

docker compose up -d

Write-Host ""
Write-Host "Backend running:"
Write-Host "http://localhost:8086/docs"
Write-Host ""
