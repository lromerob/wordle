"""Future HTTP smoke against an explicitly approved DISPOSABLE LOCAL Supabase stack.

Does not start services or read credentials. Never run against existing data.
The operator must verify that FastAPI uses LOCAL Supabase, not memory/production.
The new local database must contain only the existing CASAS dictionary fixture.
"""
import argparse
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--confirm-disposable-local-stack", required=True, action="store_true")
    args = parser.parse_args()
    url = urlsplit(args.base_url)
    if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "::1")
            or url.username or url.password or url.query or url.fragment or url.path not in ("", "/")):
        parser.error("Use only an explicit loopback HTTP origin without credentials")
    base = args.base_url.rstrip("/")
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise AssertionError("Redirects forbidden in local-only smoke")

    opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(path, payload=None, method="GET", expected=200):
        data = json.dumps(payload).encode() if payload is not None else None
        req = Request(base + path, data=data, method=method,
                      headers={"Content-Type": "application/json"})
        try:
            response = opener.open(req, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            if response.status != expected:
                raise AssertionError(f"Unexpected HTTP status: {response.status}, expected {expected}")
            return json.loads(response.read())

    assert request("/health") == {"status": "ok"}
    # Unique synthetic user; its stats are isolated. These are test writes, not seeds.
    import uuid
    user = "fin01b-" + str(uuid.uuid4())
    game = request("/game/nueva?usuario_id=" + user, method="POST")["partida_id"]
    assert str(uuid.UUID(game)) == game
    active = request("/game/" + game)
    assert "palabra_secreta" not in active["partida"]
    assert active["partida"]["intentos_usados"] == 0
    body = {"partida_id": game, "usuario_id": user, "palabra": "CASA"}
    request("/game/intento", body, "POST", 400)
    body["palabra"] = "ZZZZZ"
    request("/game/intento", body, "POST", 400)
    body["palabra"] = "CASAS"
    body["usuario_id"] = "another-synthetic-user"
    request("/game/intento", body, "POST", 403)
    body["usuario_id"] = user
    win = request("/game/intento", body, "POST")
    assert win["estado"] == "ganada" and win["intentos_usados"] == 1
    assert [item["estado"] for item in win["resultado"]] == ["correcto"] * 5
    request("/game/intento", body, "POST", 400)
    stats = request("/stats/" + user)
    assert stats["partidas_jugadas"] == 1 and stats["partidas_ganadas"] == 1
    assert stats["intentos_promedio"] == 1
    # Loss/repeated-letter scenarios remain in existing MemoryDB tests; they are
    # not claimed as SQL/API integration checks by this single-word smoke.
    print("PASS: local HTTP contracts; schema/persistence/RLS require separate SQL checks")


if __name__ == "__main__":
    main()
