"""Serve the Font Lab locally with Lab jobs: build a draft font, promote a cut, review motion.

python -X utf8 display/lab_server.py            # http://localhost:8000/display/lab/

Static files come from the repository root, exactly like `python -m http.server`.
The /api endpoints exist only here; the deployed website stays static, so its
Lab hides the job buttons. Jobs run one at a time in their own process.
"""
import argparse
from collections import deque
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOB_DIR = ROOT/'dist/lab-jobs'
KINDS = ('build', 'promote', 'motion-review', 'motion-approve')
MAX_BODY = 256*1024


class Jobs:
    """One running job at a time; finished jobs keep their log tail and result."""

    def __init__(self):
        self.lock = threading.Lock()
        self.items = {}
        self.active = None

    def start(self, kind, payload):
        with self.lock:
            if self.active and self.items[self.active]['state'] == 'running':
                return None
            job_id = time.strftime('%Y%m%d-%H%M%S-')+secrets.token_hex(3)
            folder = JOB_DIR/job_id
            folder.mkdir(parents=True)
            (folder/'input.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            job = dict(id=job_id, kind=kind, state='running', started=time.time(), log=deque(maxlen=200), result=None)
            self.items[job_id] = job
            self.active = job_id
        threading.Thread(target=self.run, args=(job, folder), daemon=True).start()
        return job_id

    def run(self, job, folder):
        script = 'motion_jobs.py' if job['kind'].startswith('motion-') else 'lab_jobs.py'
        kind = job['kind'].removeprefix('motion-')
        command = [sys.executable, '-X', 'utf8', str(HERE/script), kind,
                   '--input', str(folder/'input.json'), '--result', str(folder/'result.json')]
        try:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='replace')
            for line in process.stdout:
                job['log'].append(line.rstrip())
            process.wait()
            result_file = folder/'result.json'
            job['result'] = (json.loads(result_file.read_text(encoding='utf-8')) if result_file.exists()
                             else dict(ok=False, error='The job stopped without a result; see its log.'))
        except Exception as error:
            job['result'] = dict(ok=False, error=str(error))
        job['state'] = 'done' if job['result'].get('ok') else 'failed'

    def view(self, job_id):
        job = self.items.get(job_id)
        if not job:
            return None
        return {key: (list(value) if key == 'log' else value) for key, value in job.items()}


class LabHandler(SimpleHTTPRequestHandler):
    """Repository files plus a small same-origin job API."""

    server_version = 'SEIHouseLab/1'

    def allowed_host(self):
        """Refuse other hostnames, which blocks DNS-rebinding pages from reaching the API."""
        host = self.headers.get('Host', '')
        port = self.server.server_address[1]
        return host in {f'localhost:{port}', f'127.0.0.1:{port}', f'[::1]:{port}'}

    def end_headers(self):
        # Rebuilt fonts and pages must never come from the browser cache while working locally.
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def send_json(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.allowed_host():
            return self.send_error(403, 'Use localhost to open the Lab')
        path = urlsplit(self.path).path
        if path == '/api/lab':
            active = self.server.jobs.view(self.server.jobs.active) if self.server.jobs.active else None
            return self.send_json(200, dict(local=True, token=self.server.token, active=active))
        if path.startswith('/api/jobs/'):
            job = self.server.jobs.view(path.removeprefix('/api/jobs/'))
            return self.send_json(200, job) if job else self.send_json(404, dict(error='No such job'))
        if path.startswith('/api/'):
            return self.send_json(404, dict(error='Unknown endpoint'))
        return super().do_GET()

    def do_POST(self):
        if not self.allowed_host():
            return self.send_error(403, 'Use localhost to open the Lab')
        origin = self.headers.get('Origin')
        if origin is not None and urlsplit(origin).netloc != self.headers.get('Host'):
            return self.send_json(403, dict(error='Jobs can only start from this Lab'))
        # A custom header forces a CORS preflight, which this server never approves.
        if not secrets.compare_digest(self.headers.get('X-Lab-Token', ''), self.server.token):
            return self.send_json(403, dict(error='Reload the Lab page and try again'))
        if urlsplit(self.path).path != '/api/jobs':
            return self.send_json(404, dict(error='Unknown endpoint'))
        length = int(self.headers.get('Content-Length') or 0)
        if not 0 < length <= MAX_BODY:
            return self.send_json(413, dict(error='Request too large'))
        try:
            body = json.loads(self.rfile.read(length).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.send_json(400, dict(error='Send JSON'))
        if not isinstance(body, dict) or body.get('kind') not in KINDS:
            return self.send_json(400, dict(error='Unknown job'))
        job_id = self.server.jobs.start(body['kind'], body)
        if job_id is None:
            return self.send_json(409, dict(error='Another Lab job is still running'))
        return self.send_json(202, dict(id=job_id))

    def log_message(self, format, *args):
        # Keep the console readable: polling requests are frequent.
        # Error lines pass a status number first, so read the request line as text.
        if '/api/jobs/' not in str(args[0] if args else ''):
            super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(LabHandler, directory=str(ROOT)))
    server.token = secrets.token_urlsafe(24)
    server.jobs = Jobs()
    print(f'Font Lab: http://localhost:{args.port}/  ·  Display Lab: http://localhost:{args.port}/display/lab/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
