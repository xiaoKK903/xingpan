$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImV4cCI6MTc3ODU2MjUwMX0.695Z-6wWX7JFrqhkKULlPiRE92IRGreSrS7RfxIJnyg"
$headers = @{Authorization="Bearer $token"}
$json = "application/json"
$base = "http://localhost:8001"

function Test-Api {
    param($Name, $Uri, $Method="Get", $Body, [switch]$UseAuth)
    $h = @{"Content-Type"="$json"}
    if ($UseAuth) { $h["Authorization"] = "Bearer $token" }
    try {
        if ($Method -eq "Get") { $r = Invoke-WebRequest -Uri $Uri -Method Get -Headers $h }
        else { $r = Invoke-WebRequest -Uri $Uri -Method $Method -Headers $h -Body $Body }
        $c = $r.Content | ConvertFrom-Json
        if ($c.code -eq 200) { Write-Host "PASS: $Name" -ForegroundColor Green; return $true }
        else { Write-Host "FAIL: $Name -> $($c.message)" -ForegroundColor Red; return $false }
    } catch {
        Write-Host "FAIL: $Name -> $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host "=============== 最终 API 测试 ===============" -ForegroundColor Cyan

Write-Host "`n--- 公开接口 ---"
Test-Api "A1. 计算星盘 POST /api/astro/calculate" -Uri "$base/api/astro/calculate" -Method Post -Body '{"birth_date":"1995-06-15","birth_time":"14:30","latitude":39.9,"longitude":116.4,"birth_place":"北京"}'
Test-Api "A2. 星座列表 GET /api/astro/zodiac-signs" -Uri "$base/api/astro/zodiac-signs"
Test-Api "A3. 每日星运 GET /api/horoscope/today?sign=白羊座" -Uri "$base/api/horoscope/today?sign=%E7%99%BD%E7%BE%8A%E5%BA%A7"
Test-Api "A4. 星象气象站 POST /api/transit/calculate" -Uri "$base/api/transit/calculate" -Method Post -Body '{"birth_date":"1995-06-15","birth_time":"14:30","latitude":39.9,"longitude":116.4,"dimensions":["love","career","wealth"]}'
Test-Api "A5. 社交破冰 POST /api/social-icebreaker/card" -Uri "$base/api/social-icebreaker/card" -Method Post -Body '{"birth_date":"1995-06-15","birth_time":"14:30","latitude":39.9,"longitude":116.4}'
Test-Api "A6. 多人矩阵 POST /api/group-matrix/calculate" -Uri "$base/api/group-matrix/calculate" -Method Post -Body '{"members":[{"name":"A","birth_date":"1995-06-15","birth_time":"14:30","latitude":39.9,"longitude":116.4},{"name":"B","birth_date":"1997-08-20","birth_time":"10:00","latitude":22.5,"longitude":114.1}]}'
Test-Api "A7. 人生剧本 POST /api/life-script/calculate" -Uri "$base/api/life-script/calculate" -Method Post -Body '{"birth_date":"1995-06-15","birth_time":"14:30","latitude":39.9,"longitude":116.4,"target_year":2028}'
Test-Api "A8. 星能共鸣配置 GET /api/star-resonance/element-info" -Uri "$base/api/star-resonance/element-info"
Test-Api "A9. 平行人生广场 GET /api/plaza/parallel-worlds" -Uri "$base/api/plaza/parallel-worlds"
Test-Api "A10. 占星师工作台 POST /api/workbench/ask" -Uri "$base/api/workbench/ask" -Method Post -Body '{"question":"我的太阳星座是什么","chart_data":{"birth_date":"1995-06-15","birth_time":"14:30","latitude":39.9,"longitude":116.4}}'

Write-Host "`n--- 需登录接口 ---"
Test-Api "B1. 获取用户信息 GET /api/users/me" -Uri "$base/api/users/me" -UseAuth
Test-Api "B2. 保存星盘 POST /api/charts" -Uri "$base/api/charts" -Method Post -Body '{"name":"测试星盘","birth_date":"1995-06-15","birth_time":"14:30","birth_place":"北京","latitude":39.9,"longitude":116.4}' -UseAuth
Test-Api "B3. 我的星盘 GET /api/charts" -Uri "$base/api/charts" -UseAuth
Test-Api "B4. VIP状态 GET /api/vip/status" -Uri "$base/api/vip/status" -UseAuth
Test-Api "B5. 签到状态 GET /api/checkin/status" -Uri "$base/api/checkin/status" -UseAuth
Test-Api "B6. 邀请码 GET /api/invite/code" -Uri "$base/api/invite/code" -UseAuth
Test-Api "B7. 邀请统计 GET /api/invite/stats" -Uri "$base/api/invite/stats" -UseAuth
Test-Api "B8. 活动列表 GET /api/activity/list" -Uri "$base/api/activity/list" -UseAuth
Test-Api "B9. 成长任务 GET /api/growth-tasks/tasks" -Uri "$base/api/growth-tasks/tasks" -UseAuth
Test-Api "B10. 话题挑战 GET /api/topic-challenge/active" -Uri "$base/api/topic-challenge/active" -UseAuth
Test-Api "B11. 排行榜配置 GET /api/leaderboards/configs" -Uri "$base/api/leaderboards/configs" -UseAuth
Test-Api "B12. 个人星运 GET /api/horoscope/personal" -Uri "$base/api/horoscope/personal" -UseAuth
Test-Api "B13. 每日CP匹配状态 GET /api/daily-cp-match/status" -Uri "$base/api/daily-cp-match/status" -UseAuth
Test-Api "B14. 领取签到奖励 GET /api/checkin/rewards" -Uri "$base/api/checkin/rewards" -UseAuth
Test-Api "B15. 时间胶囊列表 GET /api/time-capsule/list" -Uri "$base/api/time-capsule/list" -UseAuth
Test-Api "B16. 前世记录 GET /api/past-life/records" -Uri "$base/api/past-life/records" -UseAuth
Test-Api "B17. PVP信息 GET /api/pk/profile" -Uri "$base/api/pk/profile" -UseAuth
Test-Api "B18. 礼物商城 GET /api/gifts/shop" -Uri "$base/api/gifts/shop" -UseAuth
Test-Api "B19. 报告商城 GET /api/report-shop/products" -Uri "$base/api/report-shop/products" -UseAuth
Test-Api "B20. 成长任务弹窗状态 GET /api/growth-tasks/popup-status" -Uri "$base/api/growth-tasks/popup-status" -UseAuth
Test-Api "B21. 星光广场帖子 GET /api/social-plaza/posts" -Uri "$base/api/social-plaza/posts" -UseAuth
Test-Api "B22. 星能共鸣状态 GET /api/star-resonance/status" -Uri "$base/api/star-resonance/status" -UseAuth

Write-Host "`n--- 管理后台接口 ---"
Test-Api "C1. 用户管理 GET /api/users/list" -Uri "$base/api/users/list" -UseAuth
Test-Api "C2. 话题管理 GET /api/topic-challenge/list" -Uri "$base/api/topic-challenge/list" -UseAuth

Write-Host "`n=============== 测试完成 ===============" -ForegroundColor Cyan
