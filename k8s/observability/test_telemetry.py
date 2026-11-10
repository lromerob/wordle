"""Focused offline checks for optional telemetry; no application suite or external calls."""
import asyncio
import importlib.util
import json
from pathlib import Path
import queue
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
spec = importlib.util.spec_from_file_location("demo_telemetry", Path(__file__).with_name("telemetry_app.py"))
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

class TelemetryTests(unittest.TestCase):
    def request(self, code=200, route="/game/intento"):
        messages=[]
        async def inner(scope, receive, send):
            scope["route"] = SimpleNamespace(path=route)
            await send({"type":"http.response.start", "status":code, "headers":[]})
            await send({"type":"http.response.body", "body":b"unchanged"})
        async def send(message):messages.append(message)
        with patch.object(t,"application",inner), patch.object(t,"EVENTS",queue.Queue(maxsize=1)):
            asyncio.run(t.app({"type":"http","path":"/private-value","method":"POST","query_string":b"secret=do-not-capture"},None,send))
            return messages,t.EVENTS.get_nowait()
    def test_response_contract_and_trace_header(self):
        messages,packet=self.request()
        self.assertEqual(messages[-1]["body"],b"unchanged")
        self.assertEqual(messages[0]["status"],200)
        self.assertEqual(dict(messages[0]["headers"])[b"x-trace-id"].decode(),packet[-2])
    def test_no_input_values_in_telemetry(self):
        _,packet=self.request(route="/untrusted-path")
        self.assertEqual(packet[0],"unmatched")
        self.assertNotIn("private-value",repr(packet));self.assertNotIn("do-not-capture",repr(packet))
    def test_error_exports_all_three_real_otlp_shapes(self):
        _,packet=self.request(code=500)
        events=MagicMock();events.get.side_effect=[packet,StopIteration]
        captured=[]
        response=MagicMock();response.__enter__.return_value=response
        opener=MagicMock()
        def opened(request,**kwargs):captured.append(json.loads(request.data));return response
        opener.open.side_effect=opened
        with patch.object(t,"EVENTS",events),patch.object(t.urllib.request,"build_opener",return_value=opener),patch("builtins.print"):
            with self.assertRaises(StopIteration):t.export()
        self.assertEqual(len(captured),3)
        self.assertEqual(captured[0]["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["status"]["code"],2)
        self.assertEqual(captured[2]["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]["severityNumber"],17)
    def test_error_response_contract_preserved(self):
        messages,_=self.request(code=400)
        self.assertEqual(messages[0]["status"],400)

if __name__ == "__main__":unittest.main(verbosity=2)
