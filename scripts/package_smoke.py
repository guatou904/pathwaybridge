"""Install the actual wheel AND sdist outside the checkout into fresh environments."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def run(command, *, cwd, env):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    artifacts = sorted(args.dist.resolve().glob("*.whl")) + sorted(
        args.dist.resolve().glob("*.tar.gz")
    )
    if len(artifacts) != 2:
        raise SystemExit("Expected exactly one wheel and one sdist in --dist")
    out = args.out.resolve()
    checkout = Path(__file__).resolve().parents[1]
    if out == checkout or checkout in out.parents:
        raise SystemExit("Use a smoke output directory outside the checkout")
    out.mkdir(parents=True, exist_ok=False)
    env = {
        k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
    }
    results = []
    for index, artifact in enumerate(artifacts):
        work = out / str(index)
        work.mkdir()
        venv = work / "env"
        run([sys.executable, "-m", "venv", str(venv)], cwd=work, env=env)
        bindir = venv / ("Scripts" if os.name == "nt" else "bin")
        python = bindir / ("python.exe" if os.name == "nt" else "python")
        cli = bindir / ("pathwaybridge.exe" if os.name == "nt" else "pathwaybridge")
        log = run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(artifact)],
            cwd=work,
            env=env,
        )
        log += run([str(python), "-m", "pip", "check"], cwd=work, env=env)
        log += run([str(cli), "--version"], cwd=work, env=env)
        log += run([str(cli), "demo", "--out", str(work / "demo")], cwd=work, env=env)
        manifest = work / "demo/inputs/manifest.json"
        log += run([str(cli), "validate", "--manifest", str(manifest)], cwd=work, env=env)
        log += run(
            [str(cli), "build", "--manifest", str(manifest), "--out", str(work / "explicit")],
            cwd=work,
            env=env,
        )
        report = json.loads((work / "explicit/evidence.json").read_text(encoding="utf-8"))
        assert report["summary"]["records"] == 20
        assert report["summary"]["mapping_status"]["ambiguous"] == 3
        for line in (work / "explicit/SHA256SUMS").read_text(encoding="utf-8").splitlines():
            expected, name = line.split(maxsplit=1)
            assert hashlib.sha256((work / "explicit" / name).read_bytes()).hexdigest() == expected
        (work / "install.log").write_text(log, encoding="utf-8")
        results.append(
            {
                "artifact": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "status": "passed",
                "python": sys.version.split()[0],
                "records": 20,
                "checks": [
                    "fresh environment",
                    "pip check",
                    "CLI version",
                    "demo",
                    "validate",
                    "build",
                    "output hashes",
                ],
            }
        )
        print(f"PASS {artifact.name}")
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
