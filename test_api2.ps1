$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImV4cCI6MTc3ODU2MjUwMX0.695Z-6wWX7JFrqhkKULlPiRE92IRGreSrS7RfxIJnyg"
$headers = @{Authorization="Bearer $token"}
$json = "application/json"
$base = "http://localhost:8001"

Write-Host "=== 1. Horoscope /today ==="
try { $r = Invoke-WebRequest -Uri "$base/api/horoscope/today?zodiac=aries" -Method Get; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | Select-Object -ExpandProperty message) } catch { Write-Host "FAIL: $($_.Exception.Message)"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "`n=== 2. Horoscope /personal (needs chart) ==="
try { $r = Invoke-WebRequest -Uri "$base/api/horoscope/personal" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 2) } catch { Write-Host "FAIL: $($_.Exception.Message)"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "`n=== 3. Synastry /calculate (check schema) ==="
$body = '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1}'
try { $r = Invoke-WebRequest -Uri "$base/api/synastry/calculate" -Method Post -ContentType $json -Body $body; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3) } catch { Write-Host "FAIL"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "`n=== 4. Checkin /sign ==="
try { $r = Invoke-WebRequest -Uri "$base/api/checkin/sign" -Method Post -Headers $headers -ContentType $json; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3) } catch { Write-Host "FAIL"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "`n=== 5. Invite /code ==="
try { $r = Invoke-WebRequest -Uri "$base/api/invite/code" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3) } catch { Write-Host "FAIL"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "`n=== 6. Topic Challenge /active ==="
try { $r = Invoke-WebRequest -Uri "$base/api/topic-challenge/active" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3) } catch { Write-Host "FAIL"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "`n=== 7. Leaderboards /configs ==="
try { $r = Invoke-WebRequest -Uri "$base/api/leaderboards/configs" -Method Get -Headers $headers; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3) } catch { Write-Host "FAIL"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }

Write-Host "`n=== 8. Synastry Analysis /calculate-and-analyze ==="
$body2 = '{"person1_birth_date":"1995-06-15","person1_birth_time":"14:30","person1_latitude":39.9,"person1_longitude":116.4,"person2_birth_date":"1997-08-20","person2_birth_time":"10:00","person2_latitude":22.5,"person2_longitude":114.1}'
try { $r = Invoke-WebRequest -Uri "$base/api/synastry-analysis/calculate-and-analyze" -Method Post -Headers $headers -ContentType $json -Body $body2; Write-Host "PASS: $($r.StatusCode)"; ($r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3) } catch { Write-Host "FAIL"; try { Write-Host ([System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()) } catch {} }
