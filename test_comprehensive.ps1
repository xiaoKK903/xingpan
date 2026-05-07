$base = "http://localhost:8001"
$json = "application/json"

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$testUsername = "test_user_$timestamp"
$testPassword = "Test@2026!"
Write-Host "========================================"
Write-Host "Full Functional Test - User: $testUsername"
Write-Host "========================================"

# 1. Register
Write-Host "`n[1] User Registration..."
$regBody = @{username=$testUsername;password=$testPassword;email="$testUsername@test.com"} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$base/api/users/register" -Method Post -ContentType $json -Body $regBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 201 -or $c.code -eq 200) {
        Write-Host "  SUCCESS: Registered"
    } else {
        Write-Host "  FAIL: $($c.message)"
    }
} catch {
    Write-Host "  EXCEPTION: $($_.Exception.Message)"
}

# 2. Login
Write-Host "`n[2] User Login..."
$loginBody = @{username=$testUsername;password=$testPassword}
try {
    $r = Invoke-WebRequest -Uri "$base/api/users/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body $loginBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.data.access_token) {
        $token = $c.data.access_token
        Write-Host "  SUCCESS: Got token"
    }
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)"; return
}

$headers = @{Authorization="Bearer $token"; "Content-Type"=$json}

# 3. Calculate Chart
Write-Host "`n[3] Calculate Chart..."
$chartBody = @{birth_date="1995-06-15";birth_time="14:30";latitude=39.9;longitude=116.4;birth_place="Beijing"} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$base/api/astro/calculate" -Method Post -ContentType $json -Body $chartBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200 -and $c.data) {
        Write-Host "  SUCCESS: data keys = $($c.data.Keys -join ', ')"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 4. Save Chart
Write-Host "`n[4] Save Chart..."
$saveBody = @{name="TestChart";birth_date="1995-06-15";birth_time="14:30";birth_place="Beijing";latitude=39.9;longitude=116.4} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$base/api/charts" -Method Post -Headers $headers -ContentType $json -Body $saveBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200 -and $c.data.id) {
        $script:chartId = $c.data.id
        Write-Host "  SUCCESS: ChartID=$chartId"
    } else {
        Write-Host "  Return: $($c.message)"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 5. Get Charts List
Write-Host "`n[5] Get Charts List..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/charts" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) {
        Write-Host "  SUCCESS: count=$($c.data.Count)"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 6. Daily Horoscope
Write-Host "`n[6] Daily Horoscope..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/horoscope/today?sign=Aries" -Method Get
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) {
        Write-Host "  SUCCESS: date=$($c.data.date)"
    } else {
        Write-Host "  Return: $($c.code) - $($c.message)"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 7. Personal Horoscope
Write-Host "`n[7] Personal Horoscope..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/horoscope/personal" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 8. Checkin
Write-Host "`n[8] Checkin..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/checkin/sign" -Method Post -Headers $headers -ContentType $json
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) {
        Write-Host "  SUCCESS: $($c.message)"
    } else {
        Write-Host "  Return: $($c.message)"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 9. Invite Code
Write-Host "`n[9] Invite Code..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/invite/code" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200 -and $c.data) {
        Write-Host "  SUCCESS: code=$($c.data.invite_code)"
    } else {
        Write-Host "  Return: $($c.code)"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 10. Synastry Calculate
Write-Host "`n[10] Synastry Calculate..."
$synaBody = @{
    person_a=@{name="UserA";birth_date="1995-06-15";birth_time="14:30";latitude=39.9;longitude=116.4;house_system="placidus"}
    person_b=@{name="UserB";birth_date="1997-08-20";birth_time="10:00";latitude=22.5;longitude=114.1;house_system="placidus"}
} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$base/api/synastry/calculate" -Method Post -ContentType $json -Body $synaBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200 -and $c.data) {
        Write-Host "  SUCCESS: keys=$($c.data.Keys -join ', ')"
    } else {
        Write-Host "  Return: $($c.code) - $($c.message)"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 11. Synastry Deep Analysis
Write-Host "`n[11] Synastry Deep Analysis..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/synastry-analysis/calculate-and-analyze" -Method Post -Headers $headers -ContentType $json -Body $synaBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 12. Transit Calculate
Write-Host "`n[12] Transit Calculate..."
$transitBody = @{birth_date="1995-06-15";birth_time="14:30";latitude=39.9;longitude=116.4} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$base/api/transit/calculate" -Method Post -ContentType $json -Body $transitBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 13. Star Resonance
Write-Host "`n[13] Star Resonance..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/star-resonance/element-info" -Method Get
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 14. Social Icebreaker
Write-Host "`n[14] Social Icebreaker..."
$iceBody = @{birth_date="1995-06-15";birth_time="14:30";latitude=39.9;longitude=116.4} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$base/api/social-icebreaker/card" -Method Post -ContentType $json -Body $iceBody
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 15. Activities
Write-Host "`n[15] Activities..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/activity/list" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) {
        $cnt = if ($c.data.items) { $c.data.items.Count } elseif ($c.data) { $c.data.Count } else { 0 }
        Write-Host "  SUCCESS: count=$cnt"
    }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 16. Growth Tasks
Write-Host "`n[16] Growth Tasks..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/growth-tasks/tasks" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 17. VIP Status
Write-Host "`n[17] VIP Status..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/vip/status" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) {
        Write-Host "  SUCCESS: is_vip=$($c.data.vip_status.is_vip)"
    } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 18. Leaderboards
Write-Host "`n[18] Leaderboards..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/leaderboards/configs" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS: count=$($c.data.total_count)" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 19. Topic Challenge
Write-Host "`n[19] Topic Challenge..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/topic-challenge/active" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 20. Social Plaza
Write-Host "`n[20] Social Plaza..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/social-plaza/posts" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 21. Boss Battle Hall
Write-Host "`n[21] Boss Battle Hall..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/boss-battle/hall" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 22. Report Shop
Write-Host "`n[22] Report Shop..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/report-shop/products" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 23. Gift Shop
Write-Host "`n[23] Gift Shop..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/gifts/shop" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 24. Daily CP Match
Write-Host "`n[24] Daily CP Match..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/daily-cp-match/status" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

# 25. Time Capsule
Write-Host "`n[25] Time Capsule List..."
try {
    $r = Invoke-WebRequest -Uri "$base/api/time-capsule/list" -Method Get -Headers $headers
    $c = ($r.Content | ConvertFrom-Json)
    if ($c.code -eq 200) { Write-Host "  SUCCESS" } else { Write-Host "  FAIL: $($c.code)" }
} catch { Write-Host "  FAIL: $($_.Exception.Message)" }

Write-Host "`n========================================"
Write-Host "Test Complete!"
Write-Host "========================================"
