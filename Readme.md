# User

# Developer

## Setup

First, install `uv` if you haven't already:
```shell
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then set up the project:
```shell
# Sync dependencies (creates venv, generates lock file, and installs dependencies)
uv sync

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

**Note:** `uv sync` automatically:
- Creates a virtual environment (`.venv`) if it doesn't exist
- Generates/updates `uv.lock` from `pyproject.toml`
- Installs all dependencies

If you only want to update the lock file without installing:
```shell
uv lock
```

To install dependencies after updating the lock file:
```shell
uv sync
```

**Note:** Pillow is required for macOS builds to automatically convert `.ico` icons to `.icns` format.

## Run/Debug

### Windows

After setup, run the app in development mode:

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Run the app
python app.py
```

**Enable Debug Mode:**

To open the developer console for debugging, edit `app.py` and change line 147:
```python
webview.start(debug=True)  # Change from False to True
```

This will open a developer console window where you can:
- View JavaScript console logs
- Inspect the DOM
- Debug JavaScript errors
- Test the bridge API calls

**Note:** Remember to set `debug=False` before compiling for distribution.

### macOS/Linux

```shell
# Activate virtual environment
source .venv/bin/activate

# Run the app
python app.py
```

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
