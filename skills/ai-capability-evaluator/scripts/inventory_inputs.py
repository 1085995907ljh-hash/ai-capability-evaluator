#!/usr/bin/env python3
"""Read-only, bounded local inventory. Hashing is not extraction/authentication.

No candidate code execution, symlink traversal, network, or archive expansion.
Absolute paths are private provenance; never copy them into user-facing HTML.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def format_hint(path, head):
    if head.startswith(b'%PDF-'):
        return 'pdf'
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if head.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if head.startswith(b'PK\x03\x04'):
        return path.suffix.lower().lstrip('.') or 'zip'
    return path.suffix.lower().lstrip('.') or 'unknown'


def inventory(inputs, max_files=5000, max_bytes=134217728):
    rows, errors, excluded = [], [], []
    visited = 0
    truncated = False
    for raw in inputs:
        root = Path(raw).absolute()
        if root.is_symlink():
            errors.append({'path': str(root), 'error': 'symlink input not followed'})
            continue
        if not root.exists():
            errors.append({'path': str(root), 'error': 'not found'})
            continue
        if root.is_file():
            candidates = iter([root])
        elif root.is_dir():
            def walk_files(base):
                def onerror(err):
                    errors.append({'path': err.filename, 'error': str(err)})
                for directory, dirs, names in os.walk(base, followlinks=False, onerror=onerror):
                    for name in sorted(dirs[:]):
                        p = Path(directory) / name
                        if name == '.git' or p.is_symlink():
                            dirs.remove(name)
                            excluded.append({'path': str(p), 'reason': 'git internals or symlink directory'})
                    dirs.sort()
                    for name in sorted(names):
                        yield Path(directory) / name
            candidates = walk_files(root)
        else:
            errors.append({'path': str(root), 'error': 'not a regular file or directory'})
            continue
        for path in candidates:
            if visited >= max_files:
                truncated = True
                break
            visited += 1
            item = {'id': f'M-{len(rows)+1:04d}', 'path': str(path),
                    'label': str(path.relative_to(root)) if root.is_dir() else path.name,
                    'status': 'inventoried_not_read'}
            try:
                # O_NOFOLLOW also rejects a symlink substituted after enumeration.
                descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
                with os.fdopen(descriptor, 'rb') as stream:
                    import stat
                    before = os.fstat(stream.fileno())
                    if not stat.S_ISREG(before.st_mode):
                        raise ValueError('not a regular file')
                    item['size_bytes'] = before.st_size
                    if before.st_size > max_bytes:
                        item.update(status='unread_size_limit', sha256=None)
                    else:
                        digest = hashlib.sha256()
                        head = stream.read(4096)
                        digest.update(head)
                        total = len(head)
                        while True:
                            chunk = stream.read(min(1048576, max_bytes - total + 1))
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > max_bytes:
                                raise ValueError('file grew beyond read limit')
                            digest.update(chunk)
                        after = os.fstat(stream.fileno())
                        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                            raise ValueError('file changed during inventory')
                        item.update(sha256=digest.hexdigest(), format=format_hint(path, head))
            except (OSError, ValueError) as exc:
                item.update(status='unread_error', error=str(exc), sha256=None)
            rows.append(item)
        if truncated:
            break
    return {'schema_version': '1.0', 'purpose': 'inventory only; not content extraction',
            'materials': rows, 'errors': errors, 'excluded': excluded,
            'truncated': truncated, 'max_files': max_files, 'max_file_bytes': max_bytes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='+')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--max-files', type=int, default=5000)
    parser.add_argument('--max-file-bytes', type=int, default=134217728)
    args = parser.parse_args()
    if args.max_files < 1 or args.max_file_bytes < 1:
        parser.error('limits must be positive')
    # Refuse outputs nested in supplied inputs to keep originals untouched.
    destination = args.output.resolve()
    for value in args.inputs:
        source = Path(value).resolve()
        if destination == source or source in destination.parents:
            parser.error('output must be outside input paths')
    data = inventory(args.inputs, args.max_files, args.max_file_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(data['materials']), 'errors': len(data['errors']),
                      'truncated': data['truncated'], 'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
