#!/usr/bin/env powershell
# Script to update Nodal.pyproj with renamed graphics module files
# This script removes old graphics entries and adds new PascalCase versions

$projectFile = "Nodal.pyproj"

if (-not (Test-Path $projectFile)) {
    Write-Host "Error: $projectFile not found in current directory" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================================="
Write-Host "         Updating Nodal.pyproj - Graphics Module Refactor              "
Write-Host "======================================================================="
Write-Host ""

# Create backup
$backupFile = "$projectFile.backup"
if (-not (Test-Path $backupFile)) {
    Copy-Item $projectFile $backupFile
    Write-Host "[OK] Backup created: $backupFile" -ForegroundColor Green
}

# Read the project file as text for string replacement
$content = Get-Content $projectFile -Raw

Write-Host "Step 1: Removing old graphics file entries..."
Write-Host "-------------------------------------------------------------------"

# Define old graphics entries to remove
$oldEntries = @(
    '    <Compile Include="graphics\node_types.py" />',
    '    <Compile Include="graphics\note_editor.py" />',
    '    <Compile Include="graphics\port.py" />',
    '    <Compile Include="graphics\scene.py" />',
    '    <Compile Include="graphics\connection.py">',
    '    <Compile Include="graphics\node.py">',
    '    <Compile Include="graphics\node_types.py">',
    '    <Compile Include="graphics\note_editor.py">',
    '    <Compile Include="graphics\port.py">',
    '    <Compile Include="graphics\scene.py">'
)

$removedCount = 0
foreach ($oldEntry in $oldEntries) {
    if ($content -match [regex]::Escape($oldEntry)) {
        $content = $content -replace [regex]::Escape($oldEntry), ""
        Write-Host "  [REMOVE] $oldEntry" -ForegroundColor Yellow
        $removedCount++
    }
}

# Also remove any orphaned closing tags with xmlns from removed entries
$content = $content -replace '^\s*<xmlns>\s*\n\s*</xmlns>\s*\n', ""
$content = $content -replace '^\s*</xmlns>\s*\n', ""

Write-Host "  Removed: $removedCount old entries" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Adding new graphics file entries..."
Write-Host "-------------------------------------------------------------------"

# Define new graphics entries (simple format without xmlns wrapper)
$newEntries = @(
    '    <Compile Include="graphics\AboutNode.py" />',
    '    <Compile Include="graphics\BaseNode.py" />',
    '    <Compile Include="graphics\Connection.py" />',
    '    <Compile Include="graphics\ImageNode.py" />',
    '    <Compile Include="graphics\NoteEditor.py" />',
    '    <Compile Include="graphics\Port.py" />',
    '    <Compile Include="graphics\Scene.py" />',
    '    <Compile Include="graphics\Theme.py" />',
    '    <Compile Include="graphics\WarmNode.py" />'
)

# Find the location to insert (after the first ItemGroup with Compile includes)
$insertPoint = $content.IndexOf('<Compile Include="graphics\__init__.py" />')

if ($insertPoint -eq -1) {
    Write-Host "Error: Could not find insertion point in pyproj file" -ForegroundColor Red
    exit 1
}

# Find the end of that line
$endOfLine = $content.IndexOf("`n", $insertPoint)
if ($endOfLine -eq -1) {
    Write-Host "Error: Could not find line ending" -ForegroundColor Red
    exit 1
}

# Insert new entries after the __init__.py entry
$insertPosition = $endOfLine + 1
$newEntriesText = ($newEntries | ForEach-Object { "$_`n" }) -join ""
$content = $content.Substring(0, $insertPosition) + $newEntriesText + $content.Substring($insertPosition)

foreach ($entry in $newEntries) {
    Write-Host "  [ADD] $entry" -ForegroundColor Green
}

# Save the updated file
Set-Content $projectFile -Value $content

Write-Host ""
Write-Host "Step 3: Verification..."
Write-Host "-------------------------------------------------------------------"

# Read back and verify
$updatedContent = Get-Content $projectFile -Raw

$allGood = $true
foreach ($entry in $newEntries) {
    if ($updatedContent -match [regex]::Escape($entry)) {
        $fileName = $entry -replace '.*Include="([^"]*)".*', '$1'
        Write-Host "  [OK] $fileName" -ForegroundColor Green
    } else {
        $fileName = $entry -replace '.*Include="([^"]*)".*', '$1'
        Write-Host "  [MISSING] $fileName" -ForegroundColor Red
        $allGood = $false
    }
}

Write-Host ""
Write-Host "======================================================================="

if ($allGood) {
    Write-Host "                 UPDATE COMPLETED SUCCESSFULLY                       "
    Write-Host "======================================================================="
    Write-Host ""
    Write-Host "Changes Made:" -ForegroundColor Green
    Write-Host "  - Removed old graphics file references" -ForegroundColor White
    Write-Host "  - Added 9 new graphics files (PascalCase naming)" -ForegroundColor White
    Write-Host "  - Updated Nodal.pyproj" -ForegroundColor White
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Reopen the solution in Visual Studio" -ForegroundColor White
    Write-Host "  2. Click 'Reload' if VS prompts about file changes" -ForegroundColor White
    Write-Host "  3. Clean and rebuild the solution (Ctrl+Shift+B)" -ForegroundColor White
    Write-Host "  4. Verify all graphics files are in Solution Explorer" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "                   UPDATE COMPLETED WITH ERRORS                      "
    Write-Host "======================================================================="
    Write-Host ""
    Write-Host "Some files could not be verified in the .pyproj file." -ForegroundColor Red
    Write-Host "Restore from backup and try again: " -ForegroundColor Yellow
    Write-Host "  Copy-Item $backupFile $projectFile -Force" -ForegroundColor Yellow
    exit 1
}
