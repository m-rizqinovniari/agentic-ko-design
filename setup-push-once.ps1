# One-time: copy SSH key to clipboard & open GitHub "Add SSH key" page
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519.pub"
if (-not (Test-Path $keyPath)) {
    Write-Host "SSH key not found at $keyPath"
    exit 1
}
Get-Content $keyPath -Raw | Set-Clipboard
Write-Host "SSH public key copied to clipboard."
Write-Host "Opening GitHub Add SSH key page..."
Start-Process "https://github.com/settings/ssh/new?title=Laptop-BML105010007416"
Write-Host "Paste (Ctrl+V) in the Key field, then click Add SSH key."
Write-Host "After that, run: git push origin master"
