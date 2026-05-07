$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImV4cCI6MTc3ODU2MjUwMX0.695Z-6wWX7JFrqhkKULlPiRE92IRGreSrS7RfxIJnyg"
$headers = @{Authorization="Bearer $token"}
$json = "application/json"
$base = "http://localhost:8001"

Write-Host "Testing time-capsule routes (backend is /api/time-capsule, NOT /api/time-capsules)..."

# Try correct path
Write-Host "`n[1] GET /api/time-capsule (list)"
try {
    $r = Invoke-WebRequest -Uri "$base/api/time-capsule" -Method Get -Headers $headers
    Write-Host "  Status: $($r.StatusCode)"
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"
    $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
    Write-Host "  Body: $e"
}

Write-Host "`n[2] GET /api/time-capsule/quota"
try {
    $r = Invoke-WebRequest -Uri "$base/api/time-capsule/quota" -Method Get -Headers $headers
    Write-Host "  Status: $($r.StatusCode)"
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"
}

Write-Host "`n[3] GET /api/time-capsule/skins"
try {
    $r = Invoke-WebRequest -Uri "$base/api/time-capsule/skins" -Method Get -Headers $headers
    Write-Host "  Status: $($r.StatusCode)"
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"
}

Write-Host "`n[4] GET /api/time-capsules (wrong path - should 404)"
try {
    $r = Invoke-WebRequest -Uri "$base/api/time-capsules" -Method Get -Headers $headers
    Write-Host "  Status: $($r.StatusCode)"
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"
}

Write-Host "`n[5] GET /api/time-capsules/quota (wrong path)"
try {
    $r = Invoke-WebRequest -Uri "$base/api/time-capsules/quota" -Method Get -Headers $headers
    Write-Host "  Status: $($r.StatusCode)"
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"
}

Write-Host "`n[6] VIP Status detail"
try {
    $r = Invoke-WebRequest -Uri "$base/api/vip/status" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    Write-Host "  Status: $($r.StatusCode) code=$($c.code)"
    Write-Host "  Data: $($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 2)"
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"
}

Write-Host "`n[7] Report Shop detail"
try {
    $r = Invoke-WebRequest -Uri "$base/api/report-shop/shop" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    Write-Host "  Status: $($r.StatusCode) code=$($c.code)"
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"
}
