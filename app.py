import os, json, sys, csv
import webview
from pathlib import Path
from typing import Optional
from datetime import datetime

APP_NAME = "Video Marker"
HOME = Path.home()
DEFAULT_OUT = HOME / "Desktop" / "marks.csv"
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))  # works for PyInstaller & dev
ASSETS = BASE / "assets"

class Bridge:
    def __init__(self):
        self.marks = []  # seconds (float)
        self.out_path = str(DEFAULT_OUT)  # Store as string to avoid pywebview serialization issues
        # Capture app start timestamp in YYYYMMDD_HHMM format
        self.app_start_timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    # JS -> Python
    def mark(self, t_seconds: float):
        # simple debounce handled in JS; still sanity-check
        if not self.marks or abs(self.marks[-1] - t_seconds) >= 0.2:
            self.marks.append(round(t_seconds, 3))
        return {"count": len(self.marks), "last": self.marks[-1]}

    def undo(self):
        if self.marks:
            self.marks.pop()
        return {"count": len(self.marks)}

    def get_marks(self):
        return list(self.marks)

    def read_video_file(self, file_path: str):
        """Read video file and return as base64 data URL"""
        try:
            import base64
            
            path = Path(file_path)
            if not path.exists():
                return {"error": "File not found"}
            
            # Determine MIME type from extension
            mime_types = {
                '.mp4': 'video/mp4',
                '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo',
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm',
            }
            ext = path.suffix.lower()
            mime_type = mime_types.get(ext, 'video/mp4')
            
            # Read file as base64
            with path.open('rb') as f:
                file_data = f.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')
            
            return {
                "data": base64_data,
                "mime_type": mime_type,
                "file_name": path.name
            }
        except Exception as e:
            return {"error": str(e)}

    def open_video_file(self):
        """Open native file dialog to select a video file"""
        try:
            # Access the current window from webview
            if not webview.windows:
                return {"error": "Window not available"}
            
            window = webview.windows[0]
            # Try without file_types first - some platforms have different requirements
            # If needed, uncomment and adjust based on platform:
            # file_types = [('Video Files', '*.mp4 *.mov *.avi *.mkv *.webm')]
            result = window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False
                # file_types=file_types
            )
            if result and len(result) > 0:
                return {"file_path": str(result[0])}
            return {"file_path": None}  # User cancelled
        except Exception as e:
            return {"error": str(e)}

    def save_csv(self, path: Optional[str] = None, role_suffix: Optional[str] = None, last_name: Optional[str] = None):
        out = Path(path) if path else Path(self.out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        
        # Build filename with timestamp, role and last name
        # e.g., marks.csv -> 20240115_1430_mark_attending.csv
        timestamp_prefix = self.app_start_timestamp
        
        # Sanitize last name for filename (remove spaces, special chars)
        safe_last_name = ""
        if last_name:
            # Keep only alphanumeric and underscores, convert to lowercase
            safe_last_name = "".join(c.lower() if c.isalnum() or c == '_' else '_' for c in last_name.strip())
            safe_last_name = safe_last_name.strip('_')  # Remove leading/trailing underscores
        
        if out.name == "marks.csv":
            # Prepend timestamp to filename
            if role_suffix and safe_last_name:
                out = out.parent / f"{timestamp_prefix}_mark_{role_suffix}_{safe_last_name}.csv"
            elif role_suffix:
                out = out.parent / f"{timestamp_prefix}_mark_{role_suffix}.csv"
            elif safe_last_name:
                out = out.parent / f"{timestamp_prefix}_mark_{safe_last_name}.csv"
            else:
                # Default case: just timestamp and mark
                out = out.parent / f"{timestamp_prefix}_mark.csv"
        else:
            # If custom filename, prepend timestamp and insert suffix before .csv
            stem = out.stem
            parts = [timestamp_prefix, stem]
            if role_suffix:
                parts.append(role_suffix)
            if safe_last_name:
                parts.append(safe_last_name)
            out = out.parent / f"{'_'.join(parts)}{out.suffix}"

        with out.open("w", newline="") as f:
            import csv
            w = csv.writer(f)
            w.writerow(["timestamp_seconds"])
            for s in self.marks:
                w.writerow([f"{s:.3f}"])

        # IMPORTANT: convert Path → str
        return {
            "saved_to": str(out),
            "count": len(self.marks),
        }

def main():
    bridge = Bridge()
    html_path = str((ASSETS / "index.html").resolve())

    # Local file URL + permission to load local assets
    # We use blob URLs for video files to avoid file:// security restrictions
    window = webview.create_window(
        APP_NAME,
        url=html_path,
        width=1100,
        height=700,
        resizable=True,
        easy_drag=False,
        confirm_close=True,
        js_api=bridge,
    )

    webview.start(debug=False)  # Set to True to enable developer console

if __name__ == "__main__":
    main()
