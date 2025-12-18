# Test API Connection Script
Write-Host "Testing API Connection..." -ForegroundColor Cyan

# Test health endpoint
try {
    Write-Host ""
    Write-Host "Testing /api/v1/health..." -ForegroundColor Yellow
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get
    Write-Host "Health check passed" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Red
}

# Test statistics endpoint
try {
    Write-Host ""
    Write-Host "Testing /api/v1/statistics..." -ForegroundColor Yellow
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/statistics" -Method Get
    Write-Host "Statistics endpoint working" -ForegroundColor Green
    $stats | ConvertTo-Json
} catch {
    Write-Host "Statistics failed: $_" -ForegroundColor Red
}

# Test analyze endpoint
try {
    Write-Host ""
    Write-Host "Testing /api/v1/analyze..." -ForegroundColor Yellow
    $body = @{
        source_ip = "192.168.1.100"
        method = "GET"
        path = "/api/users?id=1' OR '1'='1"
        headers = @{
            "User-Agent" = "Mozilla/5.0"
        }
        body = ""
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analyze" -Method Post -Body $body -ContentType "application/json"
    Write-Host "Analysis endpoint working" -ForegroundColor Green
    $result | ConvertTo-Json
} catch {
    Write-Host "Analysis failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "API Testing Complete!" -ForegroundColor Cyan
