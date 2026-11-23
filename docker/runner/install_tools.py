"""Build-only official downloads with published SHA-256 verification. No credentials."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request
import zipfile


def fetch(url):
    with urllib.request.urlopen(url, timeout=180) as response:
        return response.read()


def checked(url, expected):
    raw = fetch(url)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Official download checksum mismatch")
    return raw


def binary(path, data):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data); p.chmod(0o755)


def install():
    base = "https://releases.hashicorp.com/terraform/1.9.8/"
    name = "terraform_1.9.8_linux_amd64.zip"
    sums = fetch(base + "terraform_1.9.8_SHA256SUMS").decode().splitlines()
    expected = next(line.split()[0] for line in sums if line.split()[-1] == name)
    with zipfile.ZipFile(io.BytesIO(checked(base + name, expected))) as archive:
        binary("/usr/local/bin/terraform", archive.read("terraform"))
    url = "https://dl.k8s.io/release/v1.35.3/bin/linux/amd64/kubectl"
    binary("/usr/local/bin/kubectl", checked(url, fetch(url + ".sha256").decode().strip()))
    url = "https://github.com/Azure/kubelogin/releases/download/v0.2.22/kubelogin-linux-amd64.zip"
    with zipfile.ZipFile(io.BytesIO(checked(url, "716cbcb1880bca8f0e976b8917d06fcfe04de2c1e737eaaabbb26e2782330119"))) as archive:
        binary("/usr/local/bin/kubelogin", archive.read("bin/linux_amd64/kubelogin"))
    base = "https://nodejs.org/dist/v24.18.0/"; name = "node-v24.18.0-linux-x64.tar.xz"
    expected = next(line.split()[0] for line in fetch(base+"SHASUMS256.txt").decode().splitlines() if line.split()[-1] == name)
    Path("/opt/node").mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(checked(base+name, expected)), mode="r:xz") as archive:
        archive.extractall("/opt/node", members=[member for member in strip_root(archive)], filter="data")
    url = "https://github.com/actions/runner/releases/download/v2.338.2/actions-runner-linux-x64-2.338.2.tar.gz"
    Path("/home/runner/actions").mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(checked(url,"baebf204307bac6193480852732f0aba2ae97b6c5597c244f4d5558390147c40")), mode="r:gz") as archive:
        archive.extractall("/home/runner/actions", filter="data")


def strip_root(archive):
    for member in archive.getmembers():
        member.name = member.name.partition("/")[2]
        if member.name:
            if member.islnk(): member.linkname = member.linkname.partition("/")[2]
            yield member


if __name__ == "__main__": install()
