"""Demo-only local webhook receiver. Retains only sanitized notification evidence."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time

EVENTS = []
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        body = json.dumps(EVENTS if self.path == "/events" else {"status": "ok"}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        if self.path != "/hook":
            self.send_error(404); return
        data = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", "0")), 65536)))
        for alert in data.get("alerts", []):
            event = {"time": time.time(), "alertname": alert.get("labels", {}).get("alertname"),
                     "status": alert.get("status"), "startsAt": alert.get("startsAt"), "endsAt": alert.get("endsAt")}
            EVENTS.append(event); print(json.dumps(event), flush=True)
        del EVENTS[:-200]
        self.send_response(200); self.end_headers()

ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
