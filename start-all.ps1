# start-all.ps1
$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

function Test-ServiceHealth {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )
    
    $startTime = Get-Date
    while ((Get-Date) -lt $startTime.AddSeconds($TimeoutSeconds)) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    return $false
}

Write-Host "🚀 Legal Consistency Checker — Запуск всех сервисов" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor DarkGray

# 1. Очистка портов
Write-Host "`n🧹 Очистка портов..." -ForegroundColor Yellow
$ports = @(8001, 8082, 6333)
foreach ($port in $ports) {
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "   ✅ Порт $port освобождён" -ForegroundColor Green
    }
}

# 2. Запуск Qdrant
Write-Host "`n🐳 Запуск Qdrant..." -ForegroundColor Yellow
if (docker ps -q --filter "name=legal-qdrant") {
    Write-Host "   ℹ️  Qdrant уже запущен" -ForegroundColor Cyan
} else {
    docker start legal-qdrant 2>$null
    if ($LASTEXITCODE -ne 0) {
        docker run -d --name legal-qdrant -p 6333:6333 --restart unless-stopped qdrant/qdrant 2>$null
    }
    Write-Host "   ✅ Qdrant запущен на порту 6333" -ForegroundColor Green
}

# 3. Запуск NLP Service в новом окне
Write-Host "`n🧠 Запуск NLP Service..." -ForegroundColor Yellow
$nlpCommand = @"
cd '$projectRoot\nlp-service'
if (Test-Path 'venv\Scripts\activate.ps1') {
    & '.\venv\Scripts\activate.ps1'
} else {
    python -m venv venv
    & '.\venv\Scripts\activate.ps1'
    pip install -r requirements.txt
}
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $nlpCommand -WindowStyle Normal

# Ждем, пока сервис станет доступен
Write-Host "   ⏳ Ожидание запуска NLP Service..." -ForegroundColor Yellow
if (Test-ServiceHealth -Url "http://localhost:8001/health" -TimeoutSeconds 30) {
    Write-Host "   ✅ NLP Service запущен на порту 8001" -ForegroundColor Green
} else {
    Write-Host "   ❌ NLP Service не запустился в течение 30 секунд" -ForegroundColor Red
    exit 1
}

# 4. Запуск Backend в новом окне
Write-Host "`n⚙️  Запуск Backend (Spring Boot)..." -ForegroundColor Yellow
$backendCommand = @"
cd '$projectRoot\backend'
if (-not (Test-Path '.mvn\wrapper\maven-wrapper.jar')) {
    mvn wrapper:wrapper -Dmaven=3.9.6 2>$null
}
.\mvnw.cmd spring-boot:run
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand -WindowStyle Normal

# Ждем, пока бэкенд станет доступен
Write-Host "   ⏳ Ожидание запуска Backend..." -ForegroundColor Yellow
if (Test-ServiceHealth -Url "http://localhost:8082/actuator/health" -TimeoutSeconds 60) {
    Write-Host "   ✅ Backend запущен на порту 8082" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend не запустился в течение 60 секунд" -ForegroundColor Red
    exit 1
}

# 5. Открываем веб-интерфейсы
Write-Host "`n🌐 Открытие веб-интерфейсов..." -ForegroundColor Cyan
Start-Process "http://localhost:8082/swagger-ui.html"
Start-Process "http://localhost:8001/docs"
Start-Process "http://localhost:6333/dashboard"

Write-Host "`n" + "=" * 60 -ForegroundColor DarkGray
Write-Host "✅ ВСЕ СЕРВИСЫ ЗАПУЩЕНЫ!" -ForegroundColor Green
Write-Host "   NLP Service:  http://localhost:8001/docs" -ForegroundColor White
Write-Host "   Backend:      http://localhost:8082/swagger-ui.html" -ForegroundColor White
Write-Host "   Qdrant:       http://localhost:6333/dashboard" -ForegroundColor White
Write-Host "`n💡 Для остановки выполните: .\stop-all.ps1" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor DarkGray