"""Optional demo ASGI telemetry adapter. No game logic, SDK dependency or sensitive input capture."""
import asyncio
from collections import defaultdict
import json
import os
import queue
import secrets
import threading
import time
import urllib.request
from app.main import app as application

ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector.wordle-observability:4318")
RELEASE = os.environ.get("WORDLE_RELEASE", "demo")
ALLOWED = {"/health", "/game/nueva", "/game/intento", "/game/{partida_id}",
           "/stats/{usuario_id}", "/stats/ranking"}
RESOURCE = {"attributes": [{"key": "service.name", "value": {"stringValue": "wordle-backend"}},
                            {"key": "service.version", "value": {"stringValue": RELEASE}}]}
EVENTS = queue.Queue(maxsize=256)
START = str(time.time_ns())
COUNTS = defaultdict(int)
DROPPED = 0


def attrs(values):
    return [{"key": k, "value": {"intValue": str(v)} if isinstance(v, int) else {"stringValue": str(v)}} for k, v in values.items()]


def export():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while True:
        route, method, code, begin, end, trace, span = EVENTS.get()
        values = {"http.route": route, "http.request.method": method, "http.response.status_code": code, "release": RELEASE}
        attributes = attrs(values)
        COUNTS[(route, method, code)] += 1
        log = {"level": "ERROR" if code >= 500 else "INFO", "service": "wordle-backend",
               "route": route, "method": method, "status": code, "trace_id": trace, "release": RELEASE}
        print(json.dumps(log, separators=(",", ":")), flush=True)
        span_data = {"traceId": trace, "spanId": span, "name": method + " " + route,
            "kind": 2, "startTimeUnixNano": str(begin), "endTimeUnixNano": str(end),
            "attributes": attributes, "status": {"code": 2 if code >= 500 else 1}}
        point = {"attributes": attributes, "startTimeUnixNano": START, "timeUnixNano": str(end),
                 "asInt": str(COUNTS[(route, method, code)])}
        duration = {"attributes": attributes, "timeUnixNano": str(end), "asDouble": (end - begin) / 1e9}
        payloads = {
            "traces": {"resourceSpans": [{"resource": RESOURCE, "scopeSpans": [{"scope": {"name": "wordle-demo-asgi"}, "spans": [span_data]}]}]},
            "metrics": {"resourceMetrics": [{"resource": RESOURCE, "scopeMetrics": [{"scope": {"name": "wordle-demo-asgi"}, "metrics": [
                {"name": "wordle_http_requests", "sum": {"aggregationTemporality": 2, "isMonotonic": True, "dataPoints": [point]}},
                {"name": "wordle_http_duration_seconds", "unit": "s", "gauge": {"dataPoints": [duration]}}]}]}]},
            "logs": {"resourceLogs": [{"resource": RESOURCE, "scopeLogs": [{"scope": {"name": "wordle-demo-asgi"}, "logRecords": [{
                "timeUnixNano": str(end), "severityNumber": 17 if code >= 500 else 9,
                "severityText": log["level"], "traceId": trace, "spanId": span,
                "body": {"stringValue": json.dumps(log, separators=(",", ":"))}}]}]}]}}
        for signal, data in payloads.items():
            try:
                req = urllib.request.Request(ENDPOINT + "/v1/" + signal, data=json.dumps(data).encode(),
                    headers={"Content-Type": "application/json"}, method="POST")
                with opener.open(req, timeout=1) as response:
                    response.read()
            except Exception:
                # Bounded best effort; never dump endpoints, payloads or credentials.
                pass
        EVENTS.task_done()


async def app(scope, receive, send):
    global DROPPED
    if scope["type"] == "lifespan":
        if not any(t.name == "wordle-telemetry" for t in threading.enumerate()):
            threading.Thread(target=export, name="wordle-telemetry", daemon=True).start()
        await application(scope, receive, send)
        return
    if scope["type"] != "http":
        await application(scope, receive, send)
        return
    if scope["path"] == "/metrics":
        ready = 0
        try:
            async with application.state.db_pool.connection(timeout=1) as connection:
                await asyncio.wait_for(connection.execute("SELECT 1 FROM public.partidas LIMIT 0"), timeout=2)
            ready = 1
        except Exception:
            pass
        body = ("wordle_backend_live 1\nwordle_backend_dependency_ready " + str(ready) +
                "\nwordle_telemetry_dropped_total " + str(DROPPED) + "\n").encode()
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain; version=0.0.4")]})
        await send({"type": "http.response.body", "body": body})
        return
    trace, span = secrets.token_hex(16), secrets.token_hex(8)
    begin, code = time.time_ns(), 500
    async def response(message):
        nonlocal code
        if message["type"] == "http.response.start":
            code = message["status"]
            message = {**message, "headers": [*message.get("headers", []), (b"x-trace-id", trace.encode())]}
        await send(message)
    try:
        await application(scope, receive, response)
    finally:
        route = getattr(scope.get("route"), "path", "unmatched")
        route = route if route in ALLOWED else "unmatched"
        method = scope.get("method", "OTHER")
        method = method if method in ("GET", "POST", "OPTIONS") else "OTHER"
        try:
            EVENTS.put_nowait((route, method, code, begin, time.time_ns(), trace, span))
        except queue.Full:
            DROPPED += 1
