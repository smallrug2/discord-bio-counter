"""Bio text builder with character-limit counting (UTF-16 code units).

Discord's "About Me" limit (256 chars) is counted in UTF-16 code units,
so emoji / non-BMP chars count as 2. This tool reports that count.

Usage examples:
    python discord_bio.py --text "Hello world" --text "Line two"
    python discord_bio.py --input bio.txt --limit 256
    type bio.txt | python discord_bio.py
    python discord_bio.py --input bio.txt --output checked.txt

Platform notes:
    Windows + Linux. Stdlib only.

Dependencies:
    Standard library only (argparse, sys, pathlib).
"""

import argparse
import sys
from pathlib import Path


def utf16_len(s):
    """Length of string in UTF-16 code units (Discord-style count)."""
    return len(s.encode("utf-16-le")) // 2


def read_bio(args):
    """Gather bio text from --text args, --input file, and/or piped stdin."""
    chunks = []
    if args.text:
        chunks.append("\n".join(args.text))
    if args.input:
        chunks.append(Path(args.input).read_text(encoding="utf-8"))
    if args.stdin or (not args.text and not args.input and not sys.stdin.isatty()):
        data = sys.stdin.read()
        if data:
            chunks.append(data)
    # Preserve blank lines inside chunks, strip one trailing newline.
    return "\n".join(c.rstrip("\n") for c in chunks)


def build_parser():
    p = argparse.ArgumentParser(description="Build bio text with UTF-16 char counting.")
    p.add_argument("--text", action="append", default=[],
                   help="Bio line (repeatable; joined with newlines).")
    p.add_argument("--input", default=None,
                   help="Read bio from this UTF-8 text file.")
    p.add_argument("--stdin", action="store_true",
                   help="Also read bio text from stdin.")
    p.add_argument("--limit", type=int, default=256,
                   help="Character limit in UTF-16 units (default: %(default)s).")
    p.add_argument("--output", default=None,
                   help="Write bio to this file (UTF-8) when within limit.")
    return p


def main(argv=None):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    args = build_parser().parse_args(argv)
    bio = read_bio(args)

    if not bio:
        print("error: no bio text given (use --text, --input, or stdin).",
              file=sys.stderr)
        return 2

    total = utf16_len(bio)
    remaining = args.limit - total
    print("total: %d / %d  (python len: %d, remaining: %d)"
          % (total, args.limit, len(bio), remaining))
    for i, line in enumerate(bio.split("\n"), 1):
        print("%d [%3d] %s" % (i, utf16_len(line), line))

    if total > args.limit:
        print("OVER LIMIT by %d chars." % (total - args.limit), file=sys.stderr)
        return 1

    print("OK: %d chars remaining." % remaining)
    if args.output:
        Path(args.output).write_text(bio, encoding="utf-8")
        print("saved to: %s" % args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
