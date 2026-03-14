# Run this as Administrator to set a System-wide variable, 
# or just run it normally to set a User-wide variable.

$logPath = "C:\Users\thisg\Desktop\Cozy Times\Nodal\logs" # <--- Change this to your actual folder!

# Create the directory if it doesn't exist
if (!(Test-Path $logPath)) {
    New-Item -ItemType Directory -Force -Path $logPath
    Write-Host "Created log directory at $logPath" -ForegroundColor Cyan
}

# Set the variable for the current User
[Environment]::SetEnvironmentVariable("COZYLOG", $logPath, "User")

Write-Host "✅ Success! `$COZYLOG is now set to $logPath" -ForegroundColor Green
Write-Host "Note: You may need to restart your terminal or IDE to see the change." -ForegroundColor Yellow