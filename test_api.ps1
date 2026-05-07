$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImV4cCI6MTc3ODU2MjUwMX0.695Z-6wWX7JFrqhkKULlPiRE92IRGreSrS7RfxIJnyg"
$headers = @{Authorization="Bearer $token"}
$json = "application/json"
$base = "http://localhost:8001"

Write-Host "=== 1. Daily Horoscope ==="
$r = Invoke-WebRequest -Uri "$base/api/horoscope/daily?zodiac=aries" -Method Get
Write-Host ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)

Write-Host "`n=== 2. Synastry Calculate ==="
$body = '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1}'
try {
    $r = Invoke-WebRequest -Uri "$base/api/synastry/calculate" -Method Post -ContentType $json -Body $body
    Write-Host ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host $_.Exception.Message
    $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
    Write-Host $e
}

Write-Host "`n=== 3. Checkin ==="
try {
    $r = Invoke-WebRequest -Uri "$base/api/checkin" -Method Post -Headers $headers -ContentType $json
    Write-Host ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host $_.Exception.Message
    $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
    Write-Host $e
}

Write-Host "`n=== 4. Invite Info ==="
try {
    $r = Invoke-WebRequest -Uri "$base/api/invite/info" -Method Get -Headers $headers
    Write-Host ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host $_.Exception.Message
    $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
    Write-Host $e
}

Write-Host "`n=== 5. Topic Challenge ==="
try {
    $r = Invoke-WebRequest -Uri "$base/api/topic-challenge/current" -Method Get -Headers $headers
    Write-Host ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host $_.Exception.Message
    $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
    Write-Host $e
}

Write-Host "`n=== 6. Leaderboards ==="
try {
    $r = Invoke-WebRequest -Uri "$base/api/leaderboards" -Method Get -Headers $headers
    Write-Host ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host $_.Exception.Message
    $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
    Write-Host $e
}

Write-Host "`n=== 7. Synastry Analysis ==="
$body2 = '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1}'
try {
    $r = Invoke-WebRequest -Uri "$base/api/synastry-analysis/calculate" -Method Post -Headers $headers -ContentType $json -Body $body2
    Write-Host ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host $_.Exception.Message
    $e = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
    Write-Host $e
}
