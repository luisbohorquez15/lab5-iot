"""Receptor de webhooks de Grafana: imprime y guarda cada alerta en /logs/alerts.log"""
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG = "/logs/alerts.log"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            data = json.loads(body)
            resumen = {
                "status": data.get("status"),
                "alertas": [
                    {"nombre": a.get("labels", {}).get("alertname"),
                     "estado": a.get("status"),
                     "inicio": a.get("startsAt"),
                     "valores": a.get("valueString")}
                    for a in data.get("alerts", [])
                ],
            }
        except Exception:
            resumen = {"raw": body.decode(errors="replace")}
        line = f"{datetime.now().isoformat(timespec='seconds')} ALERTA {json.dumps(resumen, ensure_ascii=False)}"
        print(line, flush=True)
        with open(LOG, "a") as f:
            f.write(line + "\n")
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("alert-sink escuchando en :5000", flush=True)
    HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()
