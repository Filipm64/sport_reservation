#!/usr/bin/env python3
"""Run the same project checks locally and in CI, with an isolated file DB."""
import argparse
from datetime import UTC, datetime
from importlib.metadata import distributions
import os
from pathlib import Path
import platform
import shlex
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, default=ROOT / '.ci-output' / 'check.log')
    args = parser.parse_args()
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open('w', encoding='utf-8') as log:
        def report(message):
            print(message, flush=True)
            log.write(message + '\n')
            log.flush()

        def run(command, env):
            report('\nCommand: ' + shlex.join(command))
            result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            report(result.stdout.rstrip())
            report(f'Exit code: {result.returncode}')
            return result.returncode

        report(f'Verification started: {datetime.now(UTC).isoformat()}')
        report(f'OS: {platform.platform()}')
        report(f'Python: {sys.version}')
        report(f'SQLite: {sqlite3.sqlite_version}')
        report('Installed packages: ' + ', '.join(sorted(
            f'{dist.metadata["Name"]}=={dist.version}' for dist in distributions()
        )))
        env = os.environ.copy()
        run(['git', 'rev-parse', 'HEAD'], env)
        run(['git', 'status', '--short'], env)
        # Never reuse an existing path or the application's SQLite database.
        with tempfile.TemporaryDirectory(prefix='sport-booking-check-') as directory:
            env['SPORT_BOOKING_TEST_DB'] = str(Path(directory) / 'tests.sqlite3')
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            report(f'Test DB: {env["SPORT_BOOKING_TEST_DB"]}')
            commands = [
                [sys.executable, '-m', 'pip', 'check'],
                [sys.executable, 'sport_booking/manage.py', 'check'],
                [sys.executable, 'sport_booking/manage.py', 'makemigrations', '--check', '--dry-run'],
                [sys.executable, 'scripts/update_docs.py', '--check'],
                [sys.executable, 'sport_booking/manage.py', 'test', 'reservations',
                 '--noinput', '--verbosity', '2'],
            ]
            failed = False
            for command in commands:
                if run(command, env) != 0:
                    failed = True
            report('\nVerification: FAIL' if failed else '\nVerification: PASS')
            return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
