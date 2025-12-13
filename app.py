import os, json, sys, csv
import webview
from pathlib import Path
from typing import Optional
from datetime import datetime
import http.server
import socketserver
import threading
import random
from urllib.parse import urlparse

APP_NAME = "Video Marker"
HOME = Path.home()
DEFAULT_OUT = HOME / "Desktop" / "marks.csv"
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))  # works for PyInstaller & dev
ASSETS = BASE / "assets"

def make_video_handler(video_path):
    """Factory function to create a video file handler with the video path"""
    video_path_obj = Path(video_path)
    
    class VideoFileHandler(http.server.SimpleHTTPRequestHandler):
        """Custom handler to serve video files with proper headers"""
        
        def do_GET(self):
            # Serve the video file with proper headers for streaming
            if self.path == '/' or self.path == f'/{video_path_obj.name}':
                try:
                    # Get file size
                    file_size = video_path_obj.stat().st_size
                    
                    # Handle range requests for video seeking
                    range_header = self.headers.get('Range')
                    if range_header:
                        # Parse range header
                        range_match = range_header.replace('bytes=', '').split('-')
                        start = int(range_match[0]) if range_match[0] else 0
                        end = int(range_match[1]) if range_match[1] else file_size - 1
                        
                        # Send partial content response
                        self.send_response(206)
                        self.send_header('Content-Type', 'video/mp4')
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                        self.send_header('Content-Length', str(end - start + 1))
                        self.end_headers()
                        
                        # Send requested byte range
                        with open(video_path_obj, 'rb') as f:
                            f.seek(start)
                            self.wfile.write(f.read(end - start + 1))
                    else:
                        # Send full file
                        self.send_response(200)
                        self.send_header('Content-Type', 'video/mp4')
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Content-Length', str(file_size))
                        self.end_headers()
                        with open(video_path_obj, 'rb') as f:
                            self.wfile.write(f.read())
                except Exception as e:
                    self.send_error(500, str(e))
            else:
                self.send_error(404)
        
        def log_message(self, format, *args):
            # Suppress log messages
            pass
    
    return VideoFileHandler

class Bridge:
    def __init__(self):
        self.marks = []  # seconds (float)
        self.out_path = str(DEFAULT_OUT)  # Store as string to avoid pywebview serialization issues
        # Capture app start timestamp in YYYYMMDD_HHMM format
        self.app_start_timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.video_server = None
        self.video_server_port = None

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

    def get_video_url(self, file_path: str):
        """Start a local HTTP server to serve the video file"""
        try:
            path = Path(file_path).resolve()
            if not path.exists():
                return {"error": "File not found"}
            
            # Stop existing server if any
            if self.video_server is not None:
                try:
                    self.video_server.shutdown()
                    self.video_server.server_close()
                except:
                    pass
            
            # Find an available port
            port = random.randint(8000, 8999)
            max_attempts = 50
            server_created = False
            
            for _ in range(max_attempts):
                try:
                    # Create handler class with the video path
                    handler_class = make_video_handler(path)
                    self.video_server = socketserver.TCPServer(("127.0.0.1", port), handler_class)
                    self.video_server_port = port
                    server_created = True
                    break
                except OSError:
                    port = random.randint(8000, 8999)
            
            if not server_created:
                return {"error": "Could not find available port"}
            
            # Start server in a daemon thread
            def serve():
                try:
                    self.video_server.serve_forever()
                except:
                    pass
            
            server_thread = threading.Thread(target=serve, daemon=True)
            server_thread.start()
            
            # Return HTTP URL
            video_url = f"http://127.0.0.1:{port}/{path.name}"
            
            return {
                "url": video_url,
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
