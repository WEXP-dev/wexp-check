#!/usr/bin/env python3
"""Extract a JSON file that a GitHub Actions step printed with `sha256sum <file>; cat <file>`.

usage: python3 -I extract_comparison_from_log.py <job.log> <printed path> <output file>

The job log is read as bytes and never modified. The script finds the line
`<timestamp> <sha256>  <printed path>`, then takes every following line up to and including
the first line whose content is exactly `}` (the end of the top-level JSON object printed by
`cat`). From each taken line it removes the runner's prefix: an ISO-8601 UTC timestamp with
seven fractional digits, a `Z`, and one space. Lines are re-joined with LF, the final line
included, which is how `cat` printed a file ending in a newline. It then prints the digest
announced in the log and the digest of the reconstruction, and exits 0 only if they are equal
and the reconstruction parses as JSON.
"""
import hashlib, json, re, sys

PREFIX = re.compile(rb"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{7}Z ")

def main(log_path: str, printed: str, out_path: str) -> int:
    raw = open(log_path, "rb").read()
    lines = raw.split(b"\n")
    if raw.endswith(b"\n"):
        lines = lines[:-1]
    want = None
    start = None
    for i, line in enumerate(lines):
        m = re.match(rb"^\S+ ([0-9a-f]{64})  " + re.escape(printed.encode()) + rb"\r?$", line)
        if m:
            want, start = m.group(1).decode(), i + 1
            break
    if start is None:
        print("digest line not found", file=sys.stderr)
        return 2
    body = []
    for line in lines[start:]:
        if line.endswith(b"\r"):
            print("CR in log line; refusing", file=sys.stderr)
            return 2
        m = PREFIX.match(line)
        if not m:
            print("line without timestamp prefix: %r" % line[:60], file=sys.stderr)
            return 2
        content = line[m.end():]
        body.append(content)
        if content == b"}":
            break
    else:
        print("no closing brace", file=sys.stderr)
        return 2
    data = b"\n".join(body) + b"\n"
    got = hashlib.sha256(data).hexdigest()
    open(out_path, "wb").write(data)
    json.loads(data)
    print("announced_in_log", want)
    print("reconstructed   ", got)
    print("lines", len(body), "bytes", len(data))
    return 0 if got == want else 1

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
