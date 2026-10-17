#!/usr/bin/env python3
"""Exercise the actual cpu-tests Makefile with isolated fake AM/backends."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('makefile', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
source = args.makefile.read_bytes()
root = Path(tempfile.mkdtemp(prefix='ccr-f0052-'))
# These fixtures build nothing and execute no guest code. make and sh are real.
am = root / 'am'
am.mkdir()
(am / 'backend.mk').write_text('''BINARY = ./tool
ARGS = $(NAME)
IMG = unused
NEMU_EXEC := $(BINARY) $(ARGS) $(IMG)
.PHONY: run
run:
ifeq ($(ARCH),riscv64-nemu)
\t@$(NEMU_EXEC)
else
\t@./tool $(NAME)
endif
\t@test "$(FAULT)" != post
''')
(am / 'Makefile').write_text('''.PHONY: image run
image:
\t@test "$(FAULT)" != build
run: image
\t@$(MAKE) -s -f $(AM_HOME)/backend.mk NAME=$(NAME) run
''')
tool = '''#!/usr/bin/python3
import os, sys
from pathlib import Path
with open('started', 'a') as f: f.write(sys.argv[1] + '\\n')
fault = os.environ.get('FAULT', '')
name = sys.argv[1]
npc = os.environ['ARCH'].endswith('-npc')
bad = (name == 'wrong' and fault != 'xpass') or fault == 'fail'
prefix = '1: ' if npc else '[cpu-exec.c:142] nemu: '
if fault == 'empty': sys.exit(0)
if fault == 'tool': sys.exit(7)
line = prefix + '\\033[1;31m' + ('HIT BAD TRAP' if bad else 'HIT GOOD TRAP') + '\\033[0m at pc = 0x80000000'
if npc and bad: line += ', ret code=0x1h'
print(line, flush=True)
if fault == 'abort': print('DIFF ABORT', flush=True)
if fault == 'duplicate': print(line, flush=True)
if fault == 'after-trap': sys.exit(7)
sys.exit(0 if npc else int(bad))
'''
cases = [
    ('normal', 'dummy', '', 0),
    ('ordinary-fail', 'dummy', 'fail', 2),
    ('expected-negative', 'wrong', '', 0),
    ('unexpected-success', 'wrong', 'xpass', 2),
    ('negative-build', 'wrong', 'build', 2),
    ('positive-build', 'dummy', 'build', 2),
    ('missing-tool', 'wrong', 'missing', 2),
    ('tool-after-trap', 'wrong', 'after-trap', 2),
    ('post-run-failure', 'wrong', 'post', 2),
    ('no-output', 'dummy', 'empty', 2),
    ('zero', '', '', 2),
    ('mixed', 'dummy wrong', '', 0),
    ('abort-after-good', 'dummy', 'abort', 2),
    ('duplicate-result', 'wrong', 'duplicate', 2),
]
records = []
for arch in ['riscv64-nemu', 'riscv64-npc']:
    for name, selection, fault, expected in cases:
        case = root / (arch + '-' + name)
        case.mkdir()
        (case / 'Makefile').write_bytes(source)
        (case / 'tests').mkdir()
        for test in ['dummy', 'wrong']:
            (case / 'tests' / (test + '.c')).write_text('/* fake build input */\n')
        if fault != 'missing':
            (case / 'tool').write_text(tool)
            (case / 'tool').chmod(0o755)
        # Old success evidence must not rescue this invocation.
        (case / '.result').write_text('[dummy] PASS\n[wrong] PASS\n')
        (case / 'build').mkdir()
        (case / 'build/old.bin').write_text('old successful artifact\n')
        env = {**os.environ, 'AM_HOME': str(am), 'FAULT': fault, 'ARCH': arch}
        for key in ['MAKEFLAGS', 'MFLAGS', 'MAKELEVEL', 'MAKEOVERRIDES']:
            env.pop(key, None)
        cmd = ['make', '--no-print-directory', '-j2', 'ARCH=' + arch,
               'ALL=' + selection, 'run']
        p = subprocess.run(cmd, cwd=case, env=env, capture_output=True, timeout=15)
        out = args.output / case.name
        out.mkdir()
        (out / 'stdout.log').write_bytes(p.stdout)
        (out / 'stderr.log').write_bytes(p.stderr)
        started = (case / 'started').read_text().splitlines() if (case / 'started').exists() else []
        # Copy retained logs from the repaired Makefile's printed directory.
        for line in p.stdout.decode(errors='replace').splitlines():
            if line.startswith('cpu-tests logs: '):
                shutil.copytree(line.removeprefix('cpu-tests logs: '), out / 'logs')
        records.append({'case': case.name, 'argv': cmd, 'cwd': str(case),
                        'fault': fault, 'exit': p.returncode, 'expected': expected,
                        'match': p.returncode == expected, 'started': started,
                        'old_artifact_preserved': (case / 'build/old.bin').read_text() == 'old successful artifact\n'})
result = {'makefile_sha256': hashlib.sha256(source).hexdigest(),
          'check_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'fixture_root': str(root), 'commands': records,
          'matches': sum(r['match'] for r in records), 'total': len(records)}
(args.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if all(r['match'] for r in records) else 1)
