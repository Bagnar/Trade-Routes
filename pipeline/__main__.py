"""CLI entry point: python -m pipeline <command> [options]. Commands map to modules; see README.md."""
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "extract", "rates", "validate", "assemble", "index", "monitor"):
        p = sub.add_parser(name)
        p.add_argument("--corridor")
        p.add_argument("--country")
        p.add_argument("--hs6")
        p.add_argument("--lang", default="ru")
    args = parser.parse_args(argv)
    print(f"[pipeline] '{args.command}' is not implemented yet — see docs/plan.md, stage 1.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
