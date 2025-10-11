# PowerShell script to activate virtual environment for Concerto-REST project
Write-Host "Activating virtual environment..." -ForegroundColor Green

# Check if running in PowerShell and if execution policy allows script execution
try {
    & "C:\Users\Prasanth Gudipati\Documents\Zoom\.venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
}
catch {
    Write-Host "PowerShell execution policy blocked. Using batch file instead..." -ForegroundColor Yellow
    & "C:\Users\Prasanth Gudipati\Documents\Zoom\.venv\Scripts\activate.bat"
}

Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  python tenant_uuid.py                    - Run the tenant UUID lookup script" -ForegroundColor White
Write-Host "  pip install -r requirements.txt          - Install project dependencies" -ForegroundColor White  
Write-Host "  python --version                         - Check Python version" -ForegroundColor White
Write-Host ""