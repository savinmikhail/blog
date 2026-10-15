"""Synthetic parser differences; no network, containers or real secrets."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib

result = {"json_duplicate_key": json.loads('{"mode":"safe","mode":"other"}')}
try:
    tomllib.loads('mode="safe"\nmode="other"\n')
except tomllib.TOMLDecodeError:
    result["toml_duplicate_key_rejected"] = True
else:
    result["toml_duplicate_key_rejected"] = False

with tempfile.TemporaryDirectory(prefix="config-format-probe-") as directory:
    fixture = Path(directory) / "sample.env"
    # Only prints a synthetic constant; demonstrates evaluation, no side effects.
    fixture.write_text('VALUE=$(printf synthetic-command-ran)\n')
    clean_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    commands = {
        "bash_source": ["bash", "--noprofile", "--norc", "-c", 'source ./sample.env; printf "%s" "$VALUE"'],
        "node_env_file": ["node", "--env-file=sample.env", "-e", "process.stdout.write(process.env.VALUE)"],
    }
    for name, command in commands.items():
        proc = subprocess.run(command, cwd=directory, env=clean_env, capture_output=True, text=True, check=True)
        result[name] = proc.stdout

assert result["toml_duplicate_key_rejected"]
assert result["bash_source"] == "synthetic-command-ran"
assert result["node_env_file"] == "$(printf synthetic-command-ran)"
result["versions"] = {name: subprocess.run(command, capture_output=True, text=True, check=True).stdout.splitlines()[0]
                      for name, command in {"node": ["node", "--version"], "bash": ["bash", "--version"]}.items()}
Path(__file__).with_name("format-results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
