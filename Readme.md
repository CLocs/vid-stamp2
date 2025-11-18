# User

# Developer

## Setup

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install pywebview pyinstaller pillow
```

**Note:** Pillow is required for macOS builds to automatically convert `.ico` icons to `.icns` format.

## Compile

### Windows --> dist\VideoMarkerWeb.exe
```shell
# Single file executable (recommended for distribution)
pyinstaller -F -w -n VideoMarkerWeb --icon assets/video_mark_icon.ico --add-data "assets;assets" app.py

# OR directory bundle (more reliable for file dialogs, recommended for testing)
pyinstaller --windowed --onedir -n VideoMarkerWeb --icon assets/video_mark_icon.ico --add-data "assets;assets" app.py
```

### macOS --> dist/VideoMarkerWeb.app
```shell
# Directory bundle (recommended for pywebview)
# PyInstaller will auto-convert .ico to .icns if Pillow is installed
pyinstaller --windowed --onedir -n VideoMarkerWeb --icon assets/video_mark_icon.ico --add-data "assets:assets" app.py

# Alternative: If you have a .icns file, use it directly:
# pyinstaller --windowed --onedir -n VideoMarkerWeb --icon assets/video_mark_icon.icns --add-data "assets:assets" app.py

# If Gatekeeper complains during testing:
# xattr -r -d com.apple.quarantine dist/VideoMarkerWeb.app
```

**Note:** For pywebview apps, `--onedir` (directory bundle) is often more reliable than `-F` (single file) because native file dialogs and other system integrations work better. Use `-F` for Windows if you need a single executable file for distribution.

## Distribution

### macOS
Distribute the entire `.app` bundle:
- **File to distribute:** `dist/VideoMarkerWeb.app`
- Users can double-click the `.app` file to run it
- If Gatekeeper blocks it, users can run: `xattr -r -d com.apple.quarantine VideoMarkerWeb.app`

### Windows
**If using `-F` (single file):**
- **File to distribute:** `dist/VideoMarkerWeb.exe`
- Just the single `.exe` file

**If using `--onedir` (directory bundle):**
- **Folder to distribute:** `dist/VideoMarkerWeb/`
- Distribute the entire folder containing `VideoMarkerWeb.exe` and the `_internal/` folder
- Users run `VideoMarkerWeb.exe` from within the folder
