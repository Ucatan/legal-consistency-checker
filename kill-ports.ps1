$ports = @(8001, 8080, 8081, 6333)

foreach ($port in $ports) {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($process) {
        $pid = $process.OwningProcess
        $procName = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName
        Write-Host "Port $port occupied by $procName (PID: $pid). Terminating..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "Port $port is free" -ForegroundColor Green
    }
}

Write-Host "All ports released!" -ForegroundColor Cyan