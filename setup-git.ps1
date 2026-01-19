# setup-git.ps1
$githubUser = "Ucatan"
$repoName = "legal-consistency-checker"
$token = "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"

# Настройка remote
git remote remove origin 2>$null
git remote add origin "https://$token@github.com/$githubUser/$repoName.git"

# Проверка
git remote -v
Write-Host "✅ Git remote configured successfully" -ForegroundColor Green

# Первая отправка
git push -u origin main -f
Write-Host "✅ Project pushed to GitHub" -ForegroundColor Green