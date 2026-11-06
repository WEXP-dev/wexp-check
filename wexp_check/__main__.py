"""Command line: python -m wexp_check --input <normalized-input.json> --profiles <profiles.json>"""
import argparse
import json
import math
import sys

from .core import appraise
from .tokens import check_catalog


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:  # harness decoding failure, not a Core result (REPRESENTATION, 6.2)
            raise ValueError(f"duplicate JSON object member {key!r}")
        out[key] = value
    return out


def _finite(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite number {text}")
    return value


def _constant(name):
    raise ValueError(f"non-finite number {name}")


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_pairs, parse_float=_finite, parse_constant=_constant)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m wexp_check")
    parser.add_argument("--input", required=True)
    parser.add_argument("--profiles", required=True)
    args = parser.parse_args(argv)
    try:
        profiles = load(args.profiles)
        check_catalog(profiles)
        normalized_input = load(args.input)
    except (OSError, ValueError, UnicodeDecodeError) as error:  # json errors are ValueErrors
        json.dump({"harness_error": str(error), "core_appraisal_produced": False}, sys.stderr)
        sys.stderr.write("\n")
        return 2
    json.dump(appraise(normalized_input, profiles), sys.stdout, sort_keys=True, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
