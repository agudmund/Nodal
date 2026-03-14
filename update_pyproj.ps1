#!/usr/bin/env powershell
# Script to update Nodal.pyproj with wildcard includes for automatic file detection

$projectFile = "Nodal.pyproj"

if (-not (Test-Path $projectFile)) {
    Write-Host "Error: $projectFile not found in current directory" -ForegroundColor Red
    exit 1
}

Write-Host "Updating $projectFile with wildcard patterns..." -ForegroundColor Cyan

# Read the project file
[xml]$xml = Get-Content $projectFile

# Find the ItemGroup with Compile includes
$itemGroup = $xml.Project.ItemGroup | Where-Object { $_.Compile -ne $null } | Select-Object -First 1

if ($null -eq $itemGroup) {
    Write-Host "Error: Could not find ItemGroup with Compile elements" -ForegroundColor Red
    exit 1
}

# Remove all existing Compile nodes - iterate to handle array properly
$itemGroup.SelectNodes("Compile") | ForEach-Object { $itemGroup.RemoveChild($_) } | Out-Null

# Create new wildcard Compile includes
$compileNode1 = $xml.CreateElement("Compile")
$compileNode1.SetAttribute("Include", "*.py")
$itemGroup.AppendChild($compileNode1) | Out-Null

$compileNode2 = $xml.CreateElement("Compile")
$compileNode2.SetAttribute("Include", "**\*.py")
$compileNode2.SetAttribute("Exclude", "__pycache__\**;build\**;dist\**")
$itemGroup.AppendChild($compileNode2) | Out-Null

# Save the updated file
$xml.Save((Resolve-Path $projectFile))

Write-Host "✓ Successfully updated $projectFile" -ForegroundColor Green
Write-Host "New configuration:" -ForegroundColor Green
Write-Host "  - Root .py files: *.py" -ForegroundColor White
Write-Host "  - Subdirectory .py files: **\*.py (excluding __pycache__, build, dist)" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "You can now reopen the solution in Visual Studio!" -ForegroundColor Cyan
