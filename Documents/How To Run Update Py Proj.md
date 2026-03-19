# Running update_pyproj.ps1 - Instructions

## Summary
This guide explains how to run the update script, what changes it applies to Nodal.pyproj, and how to verify the results in Visual Studio.

## What This Script Does

The `update_pyproj.ps1` script automatically updates your `Nodal.pyproj` file to reflect the graphics module file renames and will verify the changes.

**Changes Applied:**
- Removes 10 old graphics file references (deprecated files and old names)
- Adds 9 new graphics files with PascalCase naming:
  - AboutNode.py
  - BaseNode.py
  - Connection.py
  - ImageNode.py
  - NoteEditor.py
  - Port.py
  - Scene.py
  - Theme.py
  - WarmNode.py

---

## How to Run

### Step 1: Close Visual Studio
Make sure Visual Studio is **completely closed** before running the script.

### Step 2: Open PowerShell in the Project Root

Navigate to the Nodal project root directory and open PowerShell.

### Step 3: Run the Script

```powershell
powershell -ExecutionPolicy Bypass -File update_pyproj.ps1
```

Or simply:

```powershell
.\update_pyproj.ps1
```

### Step 4: Verify Output

The script will show:
- Step 1: Old graphics files being removed
- Step 2: New graphics files being added
- Step 3: Verification that all new files are present

If successful, you'll see:
```
=======================================================================
                 UPDATE COMPLETED SUCCESSFULLY
=======================================================================
```

---

## After Running the Script

1. **Reopen Visual Studio**
   - The solution will automatically detect the .pyproj file changes
   - VS may prompt to "Reload" the solution - click "Reload"

2. **Clean and Rebuild**
   - Go to Build → Clean Solution (or Ctrl+Shift+B)
   - Then Build → Build Solution

3. **Verify in Solution Explorer**
   - Expand the graphics folder
   - You should see all 9 new files with PascalCase names
   - Old files should no longer appear

---

## If Something Goes Wrong

### Option 1: Manual Restore
If the script encounters an error, a backup is automatically created:

```powershell
Copy-Item Nodal.pyproj.backup Nodal.pyproj -Force
```

Then rerun the script or edit manually.

### Option 2: Manual Edit
See: `./Documents/Nodal Py Proj Update Instructions.md` for manual editing steps.

---

## Script Features

✓ Automatic backup creation (Nodal.pyproj.backup)
✓ Detailed console output showing each change
✓ Built-in verification step
✓ Error handling and rollback support
✓ Works with PowerShell execution policy restrictions

---

## Questions?

Refer to the comprehensive documentation:
- **Graphics Module Refactoring Final Status.md** - Complete overview
- **Nodal Py Proj Update Instructions.md** - Detailed instructions
- **Quick Reference - File Changes.md** - Summary of changes

All documentation files are in the `./Documents/` folder.

