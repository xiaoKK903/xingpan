$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImV4cCI6MTc3ODU2MjUwMX0.695Z-6wWX7JFrqhkKULlPiRE92IRGreSrS7RfxIJnyg"
$headers = @{Authorization="Bearer $token"}
$json = "application/json"
$base = "http://localhost:8001"

Write-Host "=== 1. Horoscope /today (aries) ==="
try { $r = Invoke-WebRequest -Uri "$base/api/horoscope/today?zodiac=aries" -Method Get; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL: $($_.Exception.Message)" }

Write-Host "=== 2. Horoscope /personal ==="
try { $r = Invoke-WebRequest -Uri "$base/api/horoscope/personal" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL: $($_.Exception.Message)" }

Write-Host "=== 3. Synastry calculate ==="
$body1 = '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person1_name":"测试1","person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1,"person2_name":"测试2"}'
try { $r = Invoke-WebRequest -Uri "$base/api/synastry/calculate" -Method Post -ContentType $json -Body $body1; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 4. Checkin /sign ==="
try { $r = Invoke-WebRequest -Uri "$base/api/checkin/sign" -Method Post -Headers $headers -ContentType $json; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 5. Invite /code ==="
try { $r = Invoke-WebRequest -Uri "$base/api/invite/code" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 6. TopicChallenge /active ==="
try { $r = Invoke-WebRequest -Uri "$base/api/topic-challenge/active" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 7. SynastryAnalysis /calculate-and-analyze ==="
$body2 = '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person1_name":"A","person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1,"person2_name":"B"}'
try { $r = Invoke-WebRequest -Uri "$base/api/synastry-analysis/calculate-and-analyze" -Method Post -ContentType $json -Body $body2; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 8. Transit weather ==="
try { $r = Invoke-WebRequest -Uri "$base/api/transit/current" -Method Get; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 9. Social icebreaker ==="
try { $r = Invoke-WebRequest -Uri "$base/api/social-icebreaker/card" -Method Post -ContentType $json -Body '{"birth_date":"1995-06-15","birth_time":"14:30","latitude":39.9,"longitude":116.4}'; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 10. Star Resonance ==="
try { $r = Invoke-WebRequest -Uri "$base/api/star-resonance/config" -Method Get; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "=== 11. Boss battle ==="
try { $r = Invoke-WebRequest -Uri "$base/api/boss-battle/active" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)" } catch { Write-Host "FAIL:"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }
