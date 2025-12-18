# Test System Script
Write-Host "Testing WAF System..." -ForegroundColor Cyan

# Wait for backend
Write-Host "`nWaiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test health
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health"
    Write-Host "OK Backend: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "FAIL Backend not responding" -ForegroundColor Red
    exit 1
}

# Generate test attacks
Write-Host "`nGenerating test traffic..." -ForegroundColor Cyan

$attacks = @(
    @{path='/api?id=1'' OR 1=1--'; ip='192.168.1.100'; type='SQL Injection'},
    @{path='/comment'; body='<script>alert(1)</script>'; ip='10.0.0.50'; type='XSS'},
    @{path='/../etc/passwd'; ip='172.16.0.10'; type='LFI'},
    @{path='/upload'; body='<?php system("cmd"); ?>'; ip='45.155.0.100'; type='Command Injection'}
)

foreach ($attack in $attacks) {
    $body = if ($attack.body) { $attack.body } else { "" }
    $json = @{
        source_ip = $attack.ip
        method = "GET"
        path = $attack.path
        headers = @{ "User-Agent" = "TestBot" }
        body = $body
    } | ConvertTo-Json -Compress
    
    try {
        Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/analyze' -Method Post -Body $json -ContentType 'application/json' | Out-Null
        Write-Host "  OK: $($attack.type)" -ForegroundColor White
    } catch {
        Write-Host "  FAIL: $($attack.type)" -ForegroundColor Red
    }
}

# Get statistics
Write-Host "`nStatistics:" -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/statistics"
    Write-Host "  Total Requests: $($stats.analyzer.total_analyzed)" -ForegroundColor White
    Write-Host "  Anomalies: $($stats.analyzer.anomalies_detected)" -ForegroundColor Red
    Write-Host "  Detection Rate: $($stats.metrics.detection_rate_percent)%" -ForegroundColor White
} catch {
    Write-Host "  Failed to get statistics" -ForegroundColor Red
}

# Get alerts
Write-Host "`nRecent Alerts:" -ForegroundColor Yellow
try {
    $alerts = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/alerts/recent?limit=5"
    $alerts.alerts | Select-Object -First 5 | ForEach-Object {
        Write-Host "  - $($_.attack_type) from $($_.request_data.client_ip)" -ForegroundColor Red
    }
} catch {
    Write-Host "  Failed to get alerts" -ForegroundColor Red
}

Write-Host "`nTest complete!" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/api/docs" -ForegroundColor Cyan
