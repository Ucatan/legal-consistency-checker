# start-all.ps1
$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

function Test-ServiceHealth {
    param([string]$Url, [int]$TimeoutSeconds = 30)
    $startTime = Get-Date
    while ((Get-Date) -lt $startTime.AddSeconds($TimeoutSeconds)) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    return $false
}

Write-Host "🚀 Legal Consistency Checker — Запуск всех сервисов" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor DarkGray

# 1. Очистка портов
Write-Host "`n🧹 Очистка портов..." -ForegroundColor Yellow
@(8001, 8082, 6333) | ForEach-Object {
    $proc = Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue
    if ($proc) { Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue }
    Write-Host "   ✅ Порт $_ освобождён" -ForegroundColor Green
}

# 2. Qdrant
Write-Host "`n🐳 Запуск Qdrant..." -ForegroundColor Yellow
if (-not (docker ps -q --filter "name=legal-qdrant")) {
    docker run -d --name legal-qdrant -p 6333:6333 --restart unless-stopped qdrant/qdrant 2>$null
}
Write-Host "   ✅ Qdrant запущен" -ForegroundColor Green

# 3. NLP Service (КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: используем прямой путь к python.exe из venv)
Write-Host "`n🧠 Запуск NLP Service..." -ForegroundColor Yellow
$nlpPath = Join-Path $projectRoot "nlp-service"
$venvPython = Join-Path $nlpPath "venv\Scripts\python.exe"

# Гарантированная активация venv через прямой вызов python.exe
$nlpCommand = @"
cd '$nlpPath'
if (-not (Test-Path '$venvPython')) {
    Write-Host '⚠️  Создаю virtual environment...' -ForegroundColor Yellow
    python -m venv venv
    & 'venv\Scripts\pip.exe' install -r requirements.txt
}
Write-Host '🚀 Запуск NLP Service...' -ForegroundColor Cyan
& '$venvPython' -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $nlpCommand -WindowStyle Normal

# Ждём и проверяем
Write-Host "   ⏳ Ожидание запуска NLP Service..." -ForegroundColor Yellow
if (Test-ServiceHealth -Url "http://localhost:8001/health" -TimeoutSeconds 45) {
    Write-Host "   ✅ NLP Service запущен на порту 8001" -ForegroundColor Green
} else {
    Write-Host "   ❌ NLP Service не отвечает!" -ForegroundColor Red
    Write-Host "   → Проверьте окно NLP Service на ошибки" -ForegroundColor Yellow
    exit 1
}

# 4. Backend
Write-Host "`n⚙️  Запуск Backend..." -ForegroundColor Yellow
$backendCommand = @"
cd '$projectRoot\backend'
if (-not (Test-Path '.mvn\wrapper\maven-wrapper.jar')) {
    mvn wrapper:wrapper -Dmaven=3.9.6 2>`$null
}
.\mvnw.cmd spring-boot:run
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand -WindowStyle Normal

Write-Host "   ⏳ Ожидание запуска Backend..." -ForegroundColor Yellow
if (Test-ServiceHealth -Url "http://localhost:8082/actuator/health" -TimeoutSeconds 60) {
    Write-Host "   ✅ Backend запущен на порту 8082" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend не отвечает!" -ForegroundColor Red
    exit 1
}

# 5. Открываем интерфейсы
Write-Host "`n🌐 Открытие веб-интерфейсов..." -ForegroundColor Cyan
Start-Process "http://localhost:8082/swagger-ui.html"
Start-Process "http://localhost:8001/docs"
Start-Process "http://localhost:6333/dashboard"

Write-Host "`n" + "=" * 60 -ForegroundColor DarkGray
Write-Host "✅ ВСЁ РАБОТАЕТ!" -ForegroundColor Green
Write-Host "   NLP:      http://localhost:8001/docs" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8082/swagger-ui.html" -ForegroundColor White
Write-Host "   Qdrant:   http://localhost:6333/dashboard" -ForegroundColor White
Write-Host "`n💡 Остановка: .\stop-all.ps1" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor DarkGray