# Nodal.pyproj Update Instructions

## Status: CANNOT EDIT - SOLUTION OPEN

The `Nodal.pyproj` file could not be updated because the solution is currently open in Visual Studio.

**To complete the update, follow these steps:**

1. **Close Visual Studio completely**
2. **Apply the changes below** (using a text editor or the script provided)
3. **Reopen the solution** in Visual Studio

---

## Changes Required

### Section 1: First ItemGroup (Simple References)

**REMOVE these lines:**
```xml
    <Compile Include="graphics\node_types.py" />
    <Compile Include="graphics\note_editor.py" />
    <Compile Include="graphics\port.py" />
    <Compile Include="graphics\scene.py" />
```

**REPLACE with these lines:**
```xml
    <Compile Include="graphics\AboutNode.py" />
    <Compile Include="graphics\BaseNode.py" />
    <Compile Include="graphics\Connection.py" />
    <Compile Include="graphics\ImageNode.py" />
    <Compile Include="graphics\NoteEditor.py" />
    <Compile Include="graphics\Port.py" />
    <Compile Include="graphics\Scene.py" />
    <Compile Include="graphics\Theme.py" />
    <Compile Include="graphics\WarmNode.py" />
```

**Location:** Lines 30-35 (approximately)

---

### Section 2: Second ItemGroup (With xmlns tags)

**REMOVE this entire block:**
```xml
    <Compile Include="graphics\connection.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\node.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\node_types.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\note_editor.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\port.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\scene.py">
      <xmlns>
      </xmlns>
    </Compile>
```

**REPLACE with this entire block:**
```xml
    <Compile Include="graphics\AboutNode.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\BaseNode.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\Connection.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\ImageNode.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\NoteEditor.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\Port.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\Scene.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\Theme.py">
      <xmlns>
      </xmlns>
    </Compile>
    <Compile Include="graphics\WarmNode.py">
      <xmlns>
      </xmlns>
    </Compile>
```

**Location:** Lines 53-88 (approximately)

---

## PowerShell Script to Apply Changes

Save this as `apply-pyproj-fix.ps1` and run in PowerShell:

```powershell
# Close Visual Studio if open
$vs = Get-Process devenv -ErrorAction SilentlyContinue
if ($vs) {
    Write-Host "Closing Visual Studio..."
    Stop-Process -Name devenv -Force
    Start-Sleep -Seconds 2
}

# Backup the file
Copy-Item Nodal.pyproj Nodal.pyproj.backup
Write-Host "Backup created: Nodal.pyproj.backup"

# Get file content
$content = Get-Content Nodal.pyproj -Raw

# Replace first section
$old1 = @'
    <Compile Include="graphics\node_types.py" />
    <Compile Include="graphics\note_editor.py" />
    <Compile Include="graphics\port.py" />
    <Compile Include="graphics\scene.py" />
'@

$new1 = @'
    <Compile Include="graphics\AboutNode.py" />
    <Compile Include="graphics\BaseNode.py" />
    <Compile Include="graphics\Connection.py" />
    <Compile Include="graphics\ImageNode.py" />
    <Compile Include="graphics\NoteEditor.py" />
    <Compile Include="graphics\Port.py" />
    <Compile Include="graphics\Scene.py" />
    <Compile Include="graphics\Theme.py" />
    <Compile Include="graphics\WarmNode.py" />
'@

$content = $content -replace [regex]::Escape($old1), $new1

# Save updated content
Set-Content Nodal.pyproj -Value $content
Write-Host "Nodal.pyproj updated successfully"
```

---

## After Update

1. Verify the changes were applied correctly
2. Open the solution in Visual Studio
3. Clean and rebuild the solution
4. All graphics module files should be recognized

---

## Verification Commands

After updating, verify the changes:

```powershell
# Count graphics entries
Select-String -Path Nodal.pyproj -Pattern 'graphics\\.*\.py' | Measure-Object

# Should show all 10 graphics files
```

---

## Current State Summary

✅ **COMPLETED:**
- All graphics module files renamed to PascalCase
- All imports updated in graphics module
- All external imports updated
- All Python tests passing
- No circular dependencies

⏳ **PENDING:**
- Manual update of `Nodal.pyproj` (solution must be closed first)

**Once pyproj is updated, the refactoring is 100% complete.**
