"""Read-only full SHA256 audit of a frozen BA source plan on Firebird."""
import concurrent.futures
import hashlib
import json
import os
import sys
from pathlib import Path


def check(row):
    path = Path(row['path'])
    result = dict(row)
    try:
        before = path.stat()
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
                h.update(block)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Source changed during hash audit')
        result.update(sha256=h.hexdigest(), bytes=after.st_size, mtime_ns=after.st_mtime_ns,
                      status='MATCH' if row['expected_sha256'] else 'NEWLY_FINGERPRINTED')
        if row['expected_sha256'] and h.hexdigest() != row['expected_sha256']:
            result['status'] = 'MISMATCH'
    except Exception as e:
        result.update(status='ERROR', error=str(e))
    print(result['status'], row['kind'], path.name, flush=True)
    return result


if __name__ == '__main__':
    os.umask(0o007)
    plan, output = map(Path, sys.argv[1:])
    rows = json.loads(plan.read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, rows))
    failures = [r for r in results if r['status'] in ('MISMATCH', 'ERROR')]
    receipt = dict(schema='ba-full-source-audit-v1', plan_sha256=hashlib.sha256(plan.read_bytes()).hexdigest(),
                   status='FAIL' if failures else 'PASS', files=len(results), failures=len(failures), results=results,
                   interpretation='New video fingerprints identify current bytes; they do not establish an absent historical video hash')
    output.write_text(json.dumps(receipt, indent=2)+'\n')
    sys.exit(bool(failures))
