#!/usr/bin/env python3
"""CRP agent closeout: inventory or remove reproducible verification artifacts.

No symlink traversal, no files outside this CCR tree, no Git history changes.
Use only after the affected verification has finished and results are recorded.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
IMAGE = {'.img', '.raw', '.bin', '.elf', '.o', '.a', '.so', '.gch', '.d',
         '.out', '.vcd', '.fst', '.bmp', '.png', '.jpg', '.jpeg', '.webp', '.pyc'}
EVIDENCE = {'.json', '.jsonl', '.log', '.gz', '.md', '.patch'}
CONSUMERS = {'abstract-machine', 'nanos-lite', 'npc', 'cpu-tests', 'rt', 'am-kernels'}
OLD_SOURCE = {'original', 'nemu-source', 'nemu', 'am', 'compat-before-source',
              'compat-check', 'compat-check-final', 'compat-before-riscv32',
              'compat-riscv32', 'compat-before-mips32', 'compat-mips32',
              'compat-before-loongarch32r', 'compat-loongarch32r'}


def files():
    for directory, dirs, names in os.walk(ROOT, followlinks=False):
        dirs[:] = [d for d in dirs if d != '.git']
        for d in list(dirs):
            p = Path(directory) / d
            if p.is_symlink():
                dirs.remove(d)
                yield p
        for name in names:
            yield Path(directory) / name


def classify(path):
    relative = path.relative_to(ROOT)
    parts = relative.parts
    if path.name in {'.config', '.npc_config'} or path.suffix in EVIDENCE:
        if not path.is_symlink() and path.suffix == '.log' and path.stat().st_size >= 8 * 1024**2:
            return 'gzip', 'large raw log; retain lossless compressed evidence'
        return None
    if path.suffix.lower() in IMAGE:
        return 'delete', 'image/screenshot/waveform/compiled output'
    if 'local' in parts:
        rest = parts[parts.index('local') + 1:]
        generated = any(x == 'build' or x.startswith(('build-', 'obj_dir', 'sta-')) for x in rest[:-1])
        snapshot = 'source' in rest[:-1]
        snapshot |= any(x in OLD_SOURCE and any(y in {'src', 'include'} for y in rest[i + 1:-1])
                        for i, x in enumerate(rest))
        snapshot |= any(x in {'abstract-machine', 'am-kernels'} for x in rest[:-1])
        consumer = any(x == 'consumers' and i + 1 < len(rest) and rest[i + 1] in CONSUMERS
                       for i, x in enumerate(rest))
        loose_snapshot = path.name.startswith(('before-', 'after-', 'current-', 'fast-')) and path.suffix in {'.c', '.v'}
        if generated or snapshot or consumer or loose_snapshot:
            return 'delete', 'rebuildable build tree or production-source snapshot'
        if not path.is_symlink():
            with path.open('rb') as stream:
                if stream.read(4) == b'\x7fELF':
                    return 'delete', 'extensionless ELF executable'
    return None


def digest(path):
    if path.is_symlink():
        return hashlib.sha256(os.readlink(path).encode()).hexdigest()
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    receipt = args.receipt.resolve()
    receipt.relative_to(ROOT)
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
    rows = []
    for path in sorted(files()):
        action = classify(path)
        if action is None:
            continue
        st = path.lstat()
        rows.append({'path': str(path.relative_to(ROOT)), 'action': action[0], 'reason': action[1],
                     'bytes': st.st_size, 'allocated_bytes': st.st_blocks * 512,
                     'sha256': digest(path), 'symlink': path.is_symlink(),
                     'tracked': str(path.relative_to(ROOT)) in tracked, 'status': 'planned'})
    data = {'root': str(ROOT), 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'applied': args.apply, 'entries': rows}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    for row in rows if args.apply else []:
        path = ROOT / row['path']
        if digest(path) != row['sha256']:
            raise RuntimeError('artifact changed after inventory: ' + row['path'])
        if row['action'] == 'delete':
            path.unlink()
            row['status'] = 'deleted'
        else:
            target = path.with_name(path.name + '.gz')
            if target.exists():
                raise RuntimeError('refuse to overwrite existing gzip: ' + str(target))
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
                temp_path = Path(temp.name)
                with gzip.GzipFile(filename='', mode='wb', fileobj=temp, mtime=0) as archive, path.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        archive.write(block)
            # Confirm the lossless result before removing the original evidence.
            h = hashlib.sha256()
            with gzip.open(temp_path, 'rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
            if h.hexdigest() != row['sha256']:
                raise RuntimeError('gzip validation failed: ' + row['path'])
            temp_path.rename(target)
            path.unlink()
            row.update(status='gzipped', retained_as=str(target.relative_to(ROOT)),
                       retained_bytes=target.stat().st_size, retained_sha256=digest(target))
    if args.apply:
        # Empty generated directories have no recovery value; retain evidence dirs.
        for directory, dirs, names in os.walk(ROOT, topdown=False, followlinks=False):
            p = Path(directory)
            if p != ROOT and not p.is_symlink():
                try:
                    p.rmdir()
                except OSError:
                    pass
    data['summary'] = {'entries': len(rows), 'delete_files': sum(x['action'] == 'delete' for x in rows),
                       'gzip_files': sum(x['action'] == 'gzip' for x in rows),
                       'tracked_deletions': sum(x['action'] == 'delete' and x['tracked'] for x in rows),
                       'input_bytes': sum(x['bytes'] for x in rows),
                       'retained_gzip_bytes': sum(x.get('retained_bytes', 0) for x in rows)}
    receipt.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(data['summary'], ensure_ascii=False))


if __name__ == '__main__':
    main()
