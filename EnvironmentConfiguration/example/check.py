"""Behavioral checks on synthetic configuration; never use real credentials."""
import json
import os
from pathlib import Path
import subprocess
import shutil
from urllib.parse import quote
import tempfile

root = Path(__file__).resolve().parent
base = {'PATH': os.environ['PATH'], 'DB_PASSWORD_FILE': str(root/'secrets/db-password.txt')}

def run(extra, command=None):
    return subprocess.run(command or ['php', 'app/config.php'], cwd=root,
                          env={**base, **extra}, text=True, capture_output=True)

checks = {}
r = run({})
assert r.returncode == 0, r.stderr
j = json.loads(r.stdout)
assert j['DB_HOST']['public_demo_value'] == 'from-app-default'
assert j['DATABASE_URL']['exported'] is False
checks['defaults'] = 'pass'
r = run({'DB_HOST': 'from-process'})
assert r.returncode == 0, r.stderr
j = json.loads(r.stdout)
assert j['DB_HOST']['public_demo_value'] == 'from-process'
assert j['DB_HOST']['origin'] == 'process-at-bootstrap'
checks['process_override'] = 'pass'
for name, extra in [('invalid_port', {'DB_PORT': '70000'}),
                    ('invalid_boolean', {'FEATURE_NEW_CHECKOUT': 'maybe'}),
                    ('empty_host', {'DB_HOST': ''}),
                    ('invalid_host', {'DB_HOST': 'host/path'}),
                    ('invalid_database_name', {'DB_NAME': 'app?debug=true'}),
                    ('empty_user', {'DB_USER': ''}),
                    ('missing_secret', {'DB_PASSWORD_FILE': ''}),
                    ('nonexistent_secret', {'DB_PASSWORD_FILE': '/nonexistent-env-guide-password'})]:
    r = run(extra)
    assert r.returncode == 1 and r.stdout == '', (name, r.stdout, r.stderr)
    checks[name] = 'pass'
with tempfile.TemporaryDirectory() as d:
    password_file = Path(d)/'password'
    marker = 'DEMO_DOLLAR_$#?@/SECRET'
    password_file.write_text(marker+'\n')
    r = run({'DB_PASSWORD_FILE': str(password_file)})
    assert r.returncode == 0, r.stderr
    assert marker not in r.stdout+r.stderr
    assert quote(marker, safe='') not in r.stdout+r.stderr
    assert 'postgresql://' not in r.stdout+r.stderr
    checks['fake_secret_and_dsn_absent_from_output'] = 'pass'
    # Check the actual DSN, strict boolean and absence of secret export without printing values.
    command = ['php', '-r', '''
$c = require 'app/config-values.php';
$expected = 'postgresql://a%40b:DEMO_DOLLAR_%24%23%3F%40%2FSECRET@from-app-default:5432/app';
if ($c['databaseUrl'] !== $expected || $c['featureNewCheckout'] !== false
    || getenv('DATABASE_URL') !== false || getenv('DB_PASSWORD') !== false) { exit(2); }
''']
    r = run({'DB_PASSWORD_FILE': str(password_file), 'DB_USER': 'a@b'}, command)
    assert r.returncode == 0 and r.stdout == '', 'DSN encoding/false flag/export check failed'
    checks['dsn_encoding_and_false_flag'] = 'pass'
    r = run({'FEATURE_NEW_CHECKOUT': 'true'}, ['php', '-r',
            "$c = require 'app/config-values.php'; exit($c['featureNewCheckout'] === true ? 0 : 2);"])
    assert r.returncode == 0, 'true flag check failed'
    checks['true_flag'] = 'pass'
    password_file.write_text('\n')
    r = run({'DB_PASSWORD_FILE': str(password_file)})
    assert r.returncode == 1 and r.stdout == ''
    checks['empty_secret'] = 'pass'
with tempfile.TemporaryDirectory() as d:
    isolated = Path(d)
    shutil.copytree(root/'app', isolated/'app')
    (isolated/'vendor').symlink_to(root/'vendor', target_is_directory=True)
    marker = 'DEMO_PARSE_SECRET'
    (isolated/'app/.env').write_text('DB_NAME="'+marker+'\n')
    r = run({}, ['php', str(isolated/'app/config.php')])
    assert r.returncode == 1 and r.stdout == ''
    assert r.stderr.strip() == 'Configuration could not be loaded'
    assert marker not in r.stderr
    checks['parser_error_does_not_reveal_value'] = 'pass'
checks['php_version'] = subprocess.run(['php','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
(root/'local-results.json').write_text(json.dumps(checks, indent=2)+'\n')
print(json.dumps(checks, indent=2))
