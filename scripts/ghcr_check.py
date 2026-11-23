"""Read public GHCR manifests/configs, verify content hashes; never prints tokens."""
import hashlib
import json
import re
import urllib.parse
import urllib.request

ACCEPT = ", ".join(("application/vnd.oci.image.index.v1+json", "application/vnd.oci.image.manifest.v1+json",
                    "application/vnd.docker.distribution.manifest.list.v2+json", "application/vnd.docker.distribution.manifest.v2+json"))


def inspect(reference):
    match = re.fullmatch(r"ghcr.io/(lromerob/wordle-(?:backend|frontend))@(sha256:[0-9a-f]{64})", reference)
    if not match:
        raise ValueError("Only pinned project GHCR images are permitted")
    repository, root = match.groups()
    token_url = "https://ghcr.io/token?" + urllib.parse.urlencode({"service":"ghcr.io", "scope":"repository:"+repository+":pull"})
    with urllib.request.urlopen(token_url, timeout=20) as response:
        token = json.load(response)["token"]  # Anonymous pull token, memory only.
    def document(digest, blob=False):
        url = "https://ghcr.io/v2/" + repository + ("/blobs/" if blob else "/manifests/") + digest
        request = urllib.request.Request(url, headers={"Accept":ACCEPT,"Authorization":"Bearer "+token})
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024 or "sha256:"+hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("Registry content checksum mismatch")
        return json.loads(raw)
    manifest = document(root)
    runtime = {root}
    if "manifests" in manifest:
        candidates = [m for m in manifest["manifests"] if m.get("platform",{}).get("os")=="linux" and m.get("platform",{}).get("architecture")=="amd64"]
        if len(candidates) != 1:
            raise ValueError("Exactly one linux/amd64 image is required")
        digest = candidates[0]["digest"];runtime.add(digest);manifest = document(digest)
    config_digest = manifest["config"]["digest"];runtime.add(config_digest)
    config = document(config_digest, blob=True)
    if config.get("os")!="linux" or config.get("architecture")!="amd64":
        raise ValueError("Image is incompatible with the configured x86 Linux pool")
    revision = config.get("config",{}).get("Labels",{}).get("org.opencontainers.image.revision", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Missing full source revision")
    return {"reference":reference,"revision":revision,"os":"linux","architecture":"amd64","runtime_digests":sorted(runtime)}
