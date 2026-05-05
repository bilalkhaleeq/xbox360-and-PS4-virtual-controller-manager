# Developer Guide 🛠️

This document contains information for developers who want to contribute to the project, build the executable, or understand the CI/CD pipeline.

---

## 🛠️ Development Setup

To enable the **Automated Commit Prefixes** (which categorize your work for the release notes), you need to link the included Git hook after cloning the repository.

### Activate Git Hooks (Windows/PowerShell):
Run the following command in your terminal to enable the automatic `feat:`, `fix:`, etc., prefixes:

```powershell
if (!(Test-Path .git/hooks)) { New-Item -ItemType Directory .git/hooks }; @'
#!/bin/sh
python .githooks/prepare-commit-msg.py "$1"
'@ | Out-File -FilePath .git/hooks/prepare-commit-msg -Encoding ascii
```

Once activated, you can just commit naturally (e.g., `git commit -m "added xbox support"`) and the system will automatically format it to `feat: added xbox support`.

---

## 📦 Building the Executable (.exe)

If you want to package this application into a standalone Windows executable, use **PyInstaller**.

### 1. Install PyInstaller
```bash
pip install pyinstaller
```

### 2. Run the Build Command
Use the following command to bundle the script, GUI assets (`CustomTkinter`), and the gamepad drivers (`vgamepad` DLLs) into a single file:

```bash
pyinstaller --noconsole --onefile --name virtual_controller_manager --collect-all customtkinter --collect-all vgamepad virtual_controller.py
```

### 3. Locate your EXE
- Once finished, a new folder named **`dist/`** will be created.
- Your standalone **`virtual_controller_manager.exe`** will be inside it.
- **Note:** The first time you launch the `.exe`, it may take 5–10 seconds to open while it extracts itself to a temporary folder. Subsequent launches are much faster.

---

## 🤖 CI/CD with GitHub Actions

This project includes a GitHub Actions workflow to automatically build and release the application.

### How to trigger a Release:
1. **Tag your commit:** Use a version tag starting with `v` (e.g., `v1.0.0`).
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. **Automatic Build & Documentation:** GitHub Actions will detect the tag, build the `.exe`, and create a new Release.
   - **Intelligent Release Notes:** The project uses a custom `generate_release_notes.py` engine with Triple-Layer Filtering:
     - **File-Aware:** Commits touching only infrastructure (`.github/`, `.githooks/`) or documentation (`README.md`, `DEVELOPER.md`) are automatically ignored.
     - **Category-Based:** Only `feat:`, `fix:`, and `refactor:` prefixes are included.
     - **Deep-Content Filtering:** Multi-part commit messages are split, and non-app segments (e.g., "updated readme") are stripped from the final output even if they share a commit with a feature.

---

## 🏗️ Project Structure
- `virtual_controller.py`: Main application logic and GUI.
- `generate_release_notes.py`: High-signal release note generation engine.
- `.githooks/`: Contains the logic for automatic commit prefixing.
- `.github/workflows/`: Contains the CI/CD pipeline configuration.
