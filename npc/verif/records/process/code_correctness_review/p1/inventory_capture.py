#!/usr/bin/env python3
"""CCR-P1 identity capture. Reads source/Git; writes ONLY a new evidence directory.

No make/import of project code, Git mutation, network, package install, checkout,
clean or automatic source traversal through directory symlinks. Existing evidence
files are never overwritten. Use a fresh --output directory for a repeat capture.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

TARGETS = ['nemu', 'abstract-machine', 'nanos-lite', 'navy-apps']
SUPPORT_DIRS = [
    *['am-kernels/tests/' + x for x in ['am-tests', 'cpu-tests', 'alu-tests', 'locality', 'riscv-tests']],
    *['am-kernels/benchmarks/' + x for x in ['coremark', 'dhrystone', 'microbench']],
    *['am-kernels/kernels/' + x for x in ['bad-apple', 'blockchain', 'char-test', 'demo', 'flash', 'hello', 'litenes', 'nemu', 'slider', 'snake', 'thread-os', 'typing-game', 'yield-os']],
    'rt/bsp/abstract-machine',
    'npc/verif/linux/boot', 'npc/verif/linux/dtb', 'npc/verif/linux/initramfs',
    'fceux-am/src/drivers/sdl',
]
SUPPORT_FILES = [
    'Makefile', 'init.sh', '.gitignore',
    'am-kernels/.gitignore', 'am-kernels/README', 'am-kernels/LICENSE',
    'rt/.gitignore', 'npc/.gitignore', 'npc/.npc_config', 'npc/Makefile',
    'npc/csrc/include/common.h', 'npc/csrc/include/memory.h', 'npc/csrc/include/difftest.h',
    'npc/csrc/util/memory.cpp', 'npc/csrc/util/difftest.cpp', 'npc/csrc/soctest.cpp',
    'fceux-am/Makefile', 'fceux-am/README.md',
]
MISSING = {
    'nemu/src/isa/x86': 'NEMU Kconfig declares x86; implementation directory absent',
    'navy-apps/libs/compiler-rt/repo': 'compiler-rt Makefile dependency absent; no clone authorized',
    'navy-apps/apps/oslab0/repo': 'oslab0 Makefile dependency absent; no clone authorized',
    'fceux': 'navy-apps/apps/fceux/Makefile references workspace fceux; fceux-am is not silently substituted',
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def command(args, cwd, allowed=(0,), data=None):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', LC_ALL='C')
    r = subprocess.run(args, cwd=cwd, input=data, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, env=env, check=False)
    if r.returncode not in allowed:
        raise RuntimeError(f'command failed: {args[0:3]!r}; rc={r.returncode}; stderr={r.stderr.decode(errors="replace")[:400]}')
    return r.stdout

def git(repo, *args, allowed=(0,), data=None):
    return command(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'maintenance.auto=false', *args], repo, allowed, data)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--inventory-output', type=Path, help='Optional separate inventory.jsonl evidence path')
    ap.add_argument('--p0-paths', type=Path, required=True)
    a = ap.parse_args()
    root = a.workspace.resolve()
    out = a.output.resolve()
    inventory_out = a.inventory_output.resolve() if a.inventory_output else out / 'inventory.jsonl'
    if any(out == root / p or (root / p) in out.parents for p in TARGETS + SUPPORT_DIRS):
        raise SystemExit('Output must be outside reviewed source directories')
    if any(inventory_out == root / p or (root / p) in inventory_out.parents for p in TARGETS + SUPPORT_DIRS + SUPPORT_FILES):
        raise SystemExit('Inventory output must be outside reviewed source paths')
    names = ['inventory.jsonl', 'baseline.json', 'p0-delta.json', 'repositories.json',
             'directories.json', 'protected-sources.jsonl', 'p0-paths-recovered.txt', 'rg-paths-current.txt']
    if inventory_out.exists() or any((out / n).exists() for n in names):
        raise SystemExit('Refusing to overwrite existing evidence; choose a fresh --output directory')
    out.mkdir(parents=True, exist_ok=True)
    p0_dir = root / 'npc/verif/records/process/code_correctness_review'
    p0 = json.loads((p0_dir / 'p0-inventory.json').read_text())
    p0_close = json.loads((p0_dir / 'p0-closeout-validation.json').read_text())
    p0_paths = a.p0_paths.read_bytes()
    if sha(p0_paths) != p0['enumeration']['path_list_sha256']:
        raise SystemExit('P0 path-list SHA-256 mismatch; historical path identity unproved')

    entries, dirs, repo_paths = {}, {}, {root}
    def relative(p):
        try:
            return p.relative_to(root).as_posix() or '.'
        except ValueError:
            return str(p)

    def remember(p, origin):
        path = relative(p)
        entries.setdefault(path, set()).add(origin)

    def walk(start, origin):
        p = root / start
        if not p.exists() and not p.is_symlink():
            remember(p, origin)
            return
        if p.is_symlink() or not p.is_dir():
            remember(p, origin)
            return
        for d, subdirs, files in os.walk(p, followlinks=False):
            directory = Path(d)
            s = directory.lstat()
            dirs[relative(directory)] = {'path': relative(directory), 'canonical_path': relative(directory.resolve()),
                'mode': oct(stat.S_IMODE(s.st_mode)), 'scope_origin': origin}
            if '.git' in subdirs or '.git' in files:
                repo_paths.add(directory)
            for name in list(subdirs):
                q = directory / name
                if q.is_symlink():
                    remember(q, origin)
                    subdirs.remove(name)
            for name in files:
                remember(directory / name, origin)

    for p in TARGETS:
        walk(p, 'CCR-plan §3 target ' + p)
    for p in SUPPORT_DIRS:
        walk(p, 'CCR-plan A13/X03/X04 directed support: ' + p)
    for p in SUPPORT_FILES:
        remember(root / p, 'CCR-plan X01/X02/A13/X04 directed support file')
    for p in MISSING:
        remember(root / p, 'CCR-plan S05 explicit missing dependency')
    for p in list(entries):
        for q in (root / p).parents:
            if q == root.parent:
                break
            if (q / '.git').exists():
                repo_paths.add(q)

    repos, trees, status_maps = {}, {}, {}
    for repo in sorted(repo_paths, key=str):
        rp = relative(repo)
        head = git(repo, 'rev-parse', 'HEAD').decode().strip()
        tree = {}
        for rec in git(repo, 'ls-tree', '-rz', '--full-tree', 'HEAD').split(b'\0'):
            if not rec:
                continue
            left, name = rec.split(b'\t', 1)
            mode, typ, oid = left.decode().split()
            tree[name.decode(errors='surrogateescape')] = {'mode': mode, 'type': typ, 'oid': oid}
        trees[rp] = tree
        short = git(repo, 'status', '--short', '--untracked-files=all')
        z = git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all').split(b'\0')
        smap = {}
        i = 0
        while i < len(z):
            rec = z[i]; i += 1
            if not rec:
                continue
            status = rec[:2].decode()
            name = rec[3:].decode(errors='surrogateescape')
            smap[name] = status
            if 'R' in status or 'C' in status:
                i += 1
        status_maps[rp] = smap
        # No diff payload/remote URL is persisted: only identity digests.
        diff = git(repo, 'diff', '--no-ext-diff', '--no-textconv', 'HEAD', '--binary')
        repos[rp] = {'path': rp, 'head': head,
            'branch': git(repo, 'symbolic-ref', '--short', '-q', 'HEAD', allowed=(0,1)).decode().strip() or 'detached',
            'object_format': git(repo, 'rev-parse', '--show-object-format').decode().strip(),
            'status_counts': dict(collections.Counter(smap.values())), 'status_sha256': sha(short),
            'diff_binary_sha256': sha(diff),
            'upstream_identity': 'Git HEAD pinned; remote URLs intentionally not exported; upstream/local authorship not inferred',
            'local_modification_origin': 'Unknown; preexisting working tree preserved',
            'status_entries': [{'path': x, 'status': y} for x,y in sorted(smap.items())]}
        for name, meta in tree.items():
            full = relative(repo / name)
            selected = any(full == x or full.startswith(x + '/') for x in TARGETS + SUPPORT_DIRS) or full in SUPPORT_FILES
            if selected and not os.path.lexists(repo / name) and meta['type'] == 'blob':
                entries.setdefault(full, set()).add('tracked-in-HEAD absent in working tree; retained identity')

    def owner(path):
        q = root / path
        matches = [p for p in repo_paths if p == q.parent or p in q.parents]
        return max(matches, key=lambda p: len(p.parts))

    grouped = collections.defaultdict(list)
    for path in entries:
        repo = owner(path)
        grouped[relative(repo)].append((root / path).relative_to(repo).as_posix())
    ignores = {}
    for rp, paths in grouped.items():
        raw = git(root / rp, 'check-ignore', '--no-index', '--verbose', '-z', '--stdin',
                  allowed=(0,1), data=('\0'.join(paths) + '\0').encode()).split(b'\0')
        for i in range(0, len(raw)-1, 4):
            source, line, pattern, name = [x.decode(errors='surrogateescape') for x in raw[i:i+4]]
            ignores[(rp, name)] = {'source': source, 'line': int(line), 'pattern': pattern}

    rows, protected = [], []
    for path in sorted(entries):
        p = root / path
        repo = owner(path); rp = relative(repo); name = p.relative_to(repo).as_posix()
        metadata = '/.git/' in '/' + path or path.endswith('/.git')
        tree = trees[rp].get(name)
        exists = os.path.lexists(p)
        row = {'inventory_id': 'I-' + sha(path.encode())[:16], 'path': path,
            'canonical_path': relative(p.resolve()), 'scope_origin': sorted(entries[path]),
            'source_sha256': None, 'identity_sha256': None, 'line_count': None,
            'text_encoding': None, 'size_bytes': None, 'mode': None, 'entry_type': None,
            'git_repo': rp, 'git_head': repos[rp]['head'], 'git_tracked': tree is not None,
            'git_status': status_maps[rp].get(name, '  ' if tree else 'untracked_or_ignored'),
            'head_blob': tree['oid'] if tree else None, 'head_mode': tree['mode'] if tree else None,
            'ignore_rule': ignores.get((rp, name)), 'git_ignored': False,
            'is_git_metadata': metadata}
        rule = row['ignore_rule']
        row['git_ignored'] = bool(rule and not rule['pattern'].startswith('!') and not tree)
        relation = 'untracked'
        if not exists:
            row['entry_type'] = 'deleted_tracked' if tree else 'missing_dependency'
            row['absence_reason'] = MISSING.get(path, 'tracked file absent' if tree else 'declared support path absent')
            relation = 'missing'
        else:
            st = p.lstat()
            row.update(size_bytes=st.st_size, mode=oct(stat.S_IMODE(st.st_mode)))
            if p.is_symlink():
                target = os.readlink(p)
                content = os.fsencode(target)
                row.update(link_target=target, target_exists=p.exists(), link_sha256=sha(content),
                           identity_sha256=sha(content), source_sha256=sha(content), hash_semantics='symlink-text')
                row['entry_type'] = 'directory_alias' if p.is_dir() else 'symlink_file'
                row['alias_coverage_policy'] = 'Do not recurse alias; canonical target identities shared; alias/configuration gets explicit coverage row'
                if p.is_file():
                    target_bytes = p.read_bytes()
                    row['target_sha256'] = sha(target_bytes)
                    row['target_size_bytes'] = len(target_bytes)
            elif p.is_file():
                content = p.read_bytes()
                row.update(entry_type='file', source_sha256=sha(content), identity_sha256=sha(content), hash_semantics='regular-file-bytes')
                if not metadata and b'\0' not in content:
                    try:
                        content.decode('utf-8')
                        row['text_encoding'] = 'utf-8'
                    except UnicodeDecodeError:
                        row['text_encoding'] = 'non-UTF8 text candidate; encoding unconfirmed'
                    row['line_count'] = content.count(b'\n') + (bool(content) and not content.endswith(b'\n'))
            else:
                content = b''
                row['entry_type'] = 'special_file'
                row['absence_reason'] = 'Nonregular file: no content read'
            if metadata:
                relation = 'metadata'
            elif tree:
                fmt = repos[rp]['object_format']
                blob = hashlib.new(fmt, b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
                match = blob == tree['oid']
                row['working_blob'] = blob
                row['source_matches_head'] = match
                wm = '120000' if p.is_symlink() else ('100755' if st.st_mode & stat.S_IXUSR else '100644')
                relation = ('git_blob_match' if wm == tree['mode'] else 'mode_only') if match else 'content_modified'
        row['provenance'] = {'kind': 'git_metadata' if metadata else ('nested_git_worktree' if rp != '.' else 'workspace_worktree'),
            'head_relation': relation,
            'authorship': 'Unknown unless separately established from history/license; HEAD equality is not proof of pristine upstream',
            'local_modification_origin': ('Git-managed metadata identity only; non-source; no HEAD blob comparison' if metadata else
                ('Unknown; preexisting; preserve' if relation in ('mode_only', 'content_modified', 'untracked', 'missing') else 'No difference from pinned HEAD bytes/mode established by blob identity')),
            'generation': 'Not inferred from extension alone; file/module coverage records generator and S03 boundary'}
        rows.append(row)
        # Documentation/index updates are allowed in P1; protect source/config/artifacts,
        # all nested worktree files, symlinks and absent tracked/dependency entries.
        mutable_doc = p.name.lower().startswith('readme') or p.suffix.lower() == '.md'
        if not metadata and not mutable_doc:
            protected.append({k: row.get(k) for k in ['path', 'entry_type', 'canonical_path', 'identity_sha256', 'target_sha256', 'mode', 'size_bytes']})

    rg = command(['rg', '--files', '--hidden', '--no-ignore', *TARGETS], root)
    rg_paths = set(rg.decode().splitlines())
    old_paths = set(p0_paths.decode().splitlines())
    target_rows = [r for r in rows if r['path'].split('/')[0] in TARGETS]
    actual_target = {r['path'] for r in target_rows if r['entry_type'] not in ('deleted_tracked', 'missing_dependency')}
    by_path = {r['path']: r for r in rows}
    rg_only = sorted(rg_paths - actual_target)
    walk_only = sorted(actual_target - rg_paths)
    walk_explanations = [{'path': p, 'entry_type': by_path[p]['entry_type'],
                          'reason': 'rg --files without --follow omits discovered symlinks; lstat preserves the link identity without recursive alias traversal' if by_path[p]['entry_type'] in ('directory_alias', 'symlink_file') else 'explicit lstat identity not emitted by rg'} for p in walk_only]
    config_comparison = {p: {'p0_sha256': old, 'p1_sha256': sha((root/p).read_bytes()),
                            'unchanged': old == sha((root/p).read_bytes())} for p,old in p0['configuration_hashes'].items()}
    repo_comparison = {p: {'head_unchanged': repos[p]['head'] == v['head'],
                          'status_unchanged': repos[p]['status_sha256'] == v['status_sha256'],
                          'diff_unchanged': repos[p]['diff_binary_sha256'] == v['diff_binary_sha256'],
                          'untracked_unchanged': all(sha((root/n).read_bytes()) == h for n,h in v.get('untracked_sha256', {}).items())}
                       for p,v in p0_close['protected_nested'].items()}
    delta = {'task': 'CCR-P1', 'date': '2026-10-16',
        'p0_path_list_recovery': {'original_location': str(a.p0_paths), 'archived_as': 'p0-paths-recovered.txt', 'sha256': sha(p0_paths),
            'matches_p0_inventory_hash': True, 'path_count': len(old_paths),
            'method': 'Recovered exact original bytes, verified historical SHA-256, then compared path sets; ordering is not a set difference'},
        'p0_to_p1_rg': {'old_count': len(old_paths), 'current_count': len(rg_paths), 'added': sorted(rg_paths-old_paths), 'removed': sorted(old_paths-rg_paths)},
        'current_rg_vs_lstat': {'rg_only': rg_only, 'lstat_only': walk_explanations,
            'unexplained_difference': rg_only + [x['path'] for x in walk_explanations if x['entry_type'] not in ('directory_alias', 'symlink_file')]},
        'extra_identity_entries': [{'path': r['path'], 'entry_type': r['entry_type'], 'reason': r.get('absence_reason')} for r in rows if r['entry_type'] in ('deleted_tracked', 'missing_dependency')],
        'configuration_hash_comparison': config_comparison,
        'nested_protection_comparison': repo_comparison,
        'p0_symlink_comparison': [{'path': r['path'], 'target_unchanged': by_path[r['path']].get('link_target') == r['target'],
            'target_existence_unchanged': by_path[r['path']].get('target_exists') == r['target_exists']} for r in p0['symlinks']],
        'root_head_change': {'p0': p0['root_repository']['head'], 'p1': repos['.']['head'], 'explanation': 'P0 explicitly approved permitted tracked documentation commit 47b6c78; source not inferred changed'},
        'limit': 'P0 persisted path identities and six config hashes plus nested diff digests, not complete source-byte hashes. Full source-content baseline begins at P1; historical bytes beyond P0 evidence cannot be proved.'}
    baseline = {'schema_version': 1, 'task': 'CCR-P1', 'date': '2026-10-16', 'workspace': str(root),
        'collection_scope': {'targets': TARGETS, 'directed_support_directories': SUPPORT_DIRS, 'directed_support_files': SUPPORT_FILES,
            'explicit_missing_dependencies': MISSING, 'directory_symlink_policy': 'lstat aliases, never recursively follow',
            'git_metadata_policy': 'hash each on-disk metadata/object file; do not unpack object contents or export remote credentials',
            'excluded_traversal': ['whole npc build', 'whole RT-Thread OS', 'external Linux/OpenSBI', 'whole fceux-am algorithm tree']},
        'identity_counts': {'total': len(rows), 'by_entry_type': dict(collections.Counter(r['entry_type'] for r in rows)),
            'by_root': dict(collections.Counter(r['path'].split('/')[0] for r in rows)),
            'four_target_actual_files_and_symlinks': len(actual_target), 'support_and_missing': len(rows)-len(actual_target),
            'git_metadata_files': sum(r['is_git_metadata'] for r in rows), 'hidden_path_entries': sum(any(x.startswith('.') for x in Path(r['path']).parts) for r in rows),
            'git_ignored_entries': sum(r['git_ignored'] for r in rows), 'directories': len(dirs), 'protected_nonmetadata_nonmarkdown_entries': len(protected)},
        'hash_policy': {'regular': 'source_sha256 and identity_sha256 = exact file bytes',
            'symlink': 'source_sha256/identity_sha256/link_sha256 = link text; target_sha256 separately for file target',
            'missing': 'null SHA; HEAD blob recorded when tracked; never fabricated',
            'text_line_count': 'newline count plus unterminated final line, no count for NUL-containing or Git metadata files',
            'protection': 'protected-sources includes all non-Git-metadata entries except README*/Markdown; Git metadata snapshots are identities, not stable source-content assertions'},
        'p0_delta_summary': {'added': len(rg_paths-old_paths), 'removed': len(old_paths-rg_paths),
            'directory_aliases_added_to_identity': sum(by_path[p]['entry_type'] == 'directory_alias' for p in walk_only),
            'file_symlinks_added_to_identity': sum(by_path[p]['entry_type'] == 'symlink_file' for p in walk_only),
            'unexplained': len(delta['current_rg_vs_lstat']['unexplained_difference'])},
        'root_head': repos['.']['head'], 'repository_count': len(repos), 'read_only': True,
        'commands': ['lstat/read bytes/os.walk(followlinks=False)', 'rg --files --hidden --no-ignore <four target roots>',
            'git --no-optional-locks: rev-parse/symbolic-ref/ls-tree/status/check-ignore/diff --no-ext-diff --no-textconv --binary'],
        'no_production_build_tests_installs_commits': True,
        'capture_script_sha256': sha(Path(__file__).read_bytes())}
    payloads = {
        'inventory.jsonl': ''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows).encode(),
        'protected-sources.jsonl': ''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in protected).encode(),
        'repositories.json': json_bytes(repos), 'directories.json': json_bytes([dirs[p] for p in sorted(dirs)]),
        'p0-delta.json': json_bytes(delta), 'p0-paths-recovered.txt': p0_paths, 'rg-paths-current.txt': rg,
    }
    baseline['artifact_sha256'] = {(os.path.relpath(inventory_out, out) if p == 'inventory.jsonl' else p): sha(b) for p,b in payloads.items()}
    payloads['baseline.json'] = json_bytes(baseline)
    for name, data in payloads.items():
        destination = inventory_out if name == 'inventory.jsonl' else out / name
        with destination.open('xb') as f:
            f.write(data)
    print(json.dumps({'output': str(out), 'counts': baseline['identity_counts'], 'delta': baseline['p0_delta_summary']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
