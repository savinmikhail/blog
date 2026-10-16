"""Local smoke tests; fixtures have no real credentials."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent
base = {'PATH': os.environ['PATH'], 'APP_TOKEN_FILE': str(root/'secrets/demo-token.txt')}

def run(extra):
    return subprocess.run(['php', 'app/config.php'], cwd=root,
                          env={**base, **extra}, text=True, capture_output=True)

checks = {}
r = run({})
assert r.returncode == 0, r.stderr
j = json.loads(r.stdout)
assert j['DB_HOST']['public_demo_value'] == 'from-app-default'
checks['defaults'] = 'pass'
r = run({'DB_HOST': 'from-process'})
assert r.returncode == 0, r.stderr
j = json.loads(r.stdout)
assert j['DB_HOST']['public_demo_value'] == 'from-process'
assert j['DB_HOST']['origin'] == 'process-at-bootstrap'
checks['process_override'] = 'pass'
for name, extra in [('invalid_port', {'DB_PORT': '70000'}),
                    ('invalid_boolean', {'APP_DEBUG': 'maybe'}),
                    ('missing_secret', {'APP_TOKEN_FILE': ''})]:
    r = run(extra)
    assert r.returncode == 1 and r.stdout == '', (name, r.stdout, r.stderr)
    checks[name] = 'pass'
with tempfile.TemporaryDirectory() as d:
    token = Path(d)/'token'
    marker = 'DEMO_DOLLAR_$#?SECRET'
    token.write_text(marker+'\n')
    r = run({'APP_TOKEN_FILE': str(token)})
    assert r.returncode == 0
    assert marker not in r.stdout+r.stderr
    checks['fake_secret_absent_from_output'] = 'pass'
checks['php_version'] = subprocess.run(['php','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
(root/'local-results.json').write_text(json.dumps(checks, indent=2)+'\n')
print(json.dumps(checks, indent=2))
