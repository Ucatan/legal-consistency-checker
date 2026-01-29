# stop-all.ps1
Write-Host "🛑 Остановка всех сервисов..." -ForegroundColor Red
Write-Host "=" * 60 -ForegroundColor DarkGray

# Остановка окон с процессами
Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*nlp-service*" -or $_.MainWindowTitle -like "*backend*"
} | Stop-Process -Force

# Остановка Java-процессов
Get-Process -Name "java" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "✅ Backend остановлен" -ForegroundColor Green

# Остановка Python-процессов
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "✅ NLP Service остановлен" -ForegroundColor Green

# Остановка Qdrant
if (docker ps -q --filter "name=legal-qdrant") {
    docker stop legal-qdrant | Out-Null
    Write-Host "✅ Qdrant остановлен" -ForegroundColor Green
}

Write-Host "`n✨ Все сервисы остановлены" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor DarkGray