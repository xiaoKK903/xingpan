$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImV4cCI6MTc3ODU2MjUwMX0.695Z-6wWX7JFrqhkKULlPiRE92IRGreSrS7RfxIJnyg"
$headers = @{Authorization="Bearer $token"}
$json = "application/json"
$base = "http://localhost:8001"

function Get-Error($uri, $method, $body, $auth) {
    $h = @{"Content-Type"="$json"}
    if ($auth) { $h["Authorization"] = "Bearer $token" }
    try {
        if ($method -eq "Get") { $r = Invoke-WebRequest -Uri $uri -Method Get -Headers $h }
        else { $r = Invoke-WebRequest -Uri $uri -Method $method -Headers $h -Body $body }
        Write-Host "PASS $($r.StatusCode): $($r.Content)"
    } catch {
        $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
        Write-Host "ERROR: $e"
    }
}

Write-Host "=== 1. Horoscope /today 422 detail ==="
Get-Error "$base/api/horoscope/today?zodiac=aries" "Get"

Write-Host "`n=== 2. Synastry /calculate body check ==="
Get-Error "$base/api/synastry/calculate" "Post" '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1}'

Write-Host "`n=== 3. Checkin /sign error ==="
Get-Error "$base/api/checkin/sign" "Post" '{}' $true

Write-Host "`n=== 4. SynastryAnalysis 422 ==="
Get-Error "$base/api/synastry-analysis/calculate-and-analyze" "Post" '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1}' $true

Write-Host "`n=== 5. Transit current ==="
Get-Error "$base/api/transit/current" "Get"

Write-Host "`n=== 6. Star Resonance config ==="
Get-Error "$base/api/star-resonance/config" "Get"

Write-Host "`n=== 7. Boss battle active ==="
Get-Error "$base/api/boss-battle/active" "Get" $null $true
