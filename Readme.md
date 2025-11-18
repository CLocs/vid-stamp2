# User

# Developer

## Setup

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install pywebview pyinstaller qtpy
```

## Compile

### Windows --> dist\VideoMarkerWeb.exe
```shell
pyinstaller -F -w -n VideoMarkerWeb --add-data "assets;assets" app.py
```

### macOS --> dist/VideoMarkerWeb.app

```shell
pyinstaller --windowed --onedir -n VideoMarkerWeb \
  --add-data "assets:assets" \
  app.py
# Optional: --icon app.icns
# If Gatekeeper complains during testing:
# xattr -r -d com.apple.quarantine dist/VideoMarkerWeb.app
```
