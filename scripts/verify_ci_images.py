"""Record sanitized local image evidence; run isolated liveness checks by image ID.

No registry access, credentials, database, volumes or published ports are used.
Local image IDs are not evidence of a published registry manifest. Only owned containers are removed.
"""
import argparse
import json
import re
import subprocess
import time
import uuid
from pathlib import Path


def docker(*args):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=40)
    if result.returncode:
        raise RuntimeError(f'Docker {args[0]} failed (exit {result.returncode})')
    return result.stdout.strip()


def verify(image, revision, component):
    # Select metadata explicitly: never dump Config.Env, credentials or container logs.
    template = ('{"id":{{json .Id}},"size_bytes":{{json .Size}},'
                '"os":{{json .Os}},"architecture":{{json .Architecture}},'
                '"user":{{json .Config.User}},"repo_digests":{{json .RepoDigests}},'
                '"revision":{{json (index .Config.Labels "org.opencontainers.image.revision")}}}')
    info = json.loads(docker('image', 'inspect', '--format', template, image))
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', info['id']):
        raise RuntimeError('Invalid immutable image ID')
    if info['revision'] != revision or info['user'] in ('', '0', 'root', '0:0'):
        raise RuntimeError('Revision mismatch or privileged image user')
    owner = uuid.uuid4().hex
    cid = None
    try:
        cid = docker('run', '--detach', '--pull=never', '--network=none', '--read-only',
                     '--tmpfs', '/tmp:rw,noexec,nosuid,size=32m', '--cap-drop=ALL',
                     '--security-opt=no-new-privileges', '--label', f'wordle.fin04={owner}',
                     info['id'])
        if not re.fullmatch(r'[0-9a-f]{64}', cid):
            raise RuntimeError('Invalid owned container ID')
        if component == 'backend':
            check = ['python', '-c',
                     "import urllib.request; "
                     "o=urllib.request.build_opener(urllib.request.ProxyHandler({})); "
                     "r=o.open('http://127.0.0.1:8000/health',timeout=2); "
                     "assert r.status==200"]
        else:
            check = ['wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:8080/']
        for _ in range(30):
            result = subprocess.run(['docker', 'exec', cid, *check], capture_output=True, timeout=5)
            healthy = docker('inspect', '--format', '{{.State.Health.Status}}', cid)
            if result.returncode == 0 and healthy == 'healthy':
                break
            time.sleep(1)
        else:
            raise RuntimeError(f'{component}: runtime/healthcheck did not pass')
        actual_id = docker('inspect', '--format', '{{.Image}}', cid)
        if actual_id != info['id']:
            raise RuntimeError('Runtime image ID differs from inspected build')
        info.update(component=component, runtime_image_id=actual_id,
                    runtime_http_status=200, health='healthy', network='none', published_ports=False)
        return info
    finally:
        if cid and re.fullmatch(r'[0-9a-f]{64}', cid):
            label = docker('inspect', '--format', '{{index .Config.Labels "wordle.fin04"}}', cid)
            if label != owner:
                raise RuntimeError('Refusing to remove a container with a different owner label')
            docker('rm', '--force', cid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', required=True)
    parser.add_argument('--frontend', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.revision):
        parser.error('revision must be a full commit SHA')
    records = [verify(args.backend, args.revision, 'backend'),
               verify(args.frontend, args.revision, 'frontend')]
    args.output.write_text(json.dumps({'revision': args.revision,
        'digest_scope': 'local Docker image ID; not proof of publication in a registry',
        'images': records}, indent=2) + '\n', encoding='utf-8')
    print('PASS: two non-root runtimes healthy by immutable image ID; owned containers removed')


if __name__ == '__main__':
    main()
