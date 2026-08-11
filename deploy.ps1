# Deploy to GitHub
# Run after: gh auth login

$ErrorActionPreference = "Stop"

Write-Host "Creating GitHub repo and pushing..." -ForegroundColor Cyan

gh repo create web-scraper `
  --public `
  --source=. `
  --remote=origin `
  --push `
  --description "Python CLI web scraper with quotes, metadata, and link extraction"

if ($LASTEXITCODE -eq 0) {
    $url = gh repo view --json url -q .url
    Write-Host "`nDeployed successfully!" -ForegroundColor Green
    Write-Host "Repository: $url"
} else {
    Write-Host "`nDeploy failed. Make sure you are logged in: gh auth login" -ForegroundColor Red
}
