"""CLI entry point: python -m pipeline <command> [options]. Commands map to modules; see README.md."""
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "extract", "rates", "validate", "assemble", "index", "monitor", "supply"):
        p = sub.add_parser(name)
        p.add_argument("--corridor")
        p.add_argument("--country")
        p.add_argument("--hs6")
        p.add_argument("--lang", default="ru")
        p.add_argument("--url", help="fetch/extract: one page from the whitelist")
        p.add_argument("--topic", help="extract: topic hint passed to the model")
        p.add_argument("--registry", action="store_true", help="extract: every URL listed in data/sources.yaml")
        p.add_argument("--force", action="store_true", help="extract: re-run the model even if the page is unchanged")
    args = parser.parse_args(argv)

    if args.command == "fetch":
        from . import fetch

        if not args.url:
            parser.error("fetch needs --url")
        snap = fetch.fetch_url(args.url)
        print(f"{snap.http_status} {snap.url} hash={snap.content_hash[:12]} saved={snap.path}")
        return 0
    if args.command == "extract":
        from . import extract

        if args.registry:
            paths = extract.extract_registry(args.country, force=args.force)
            print(f"{len(paths)} file(s) written to data/facts")
            return 0
        if not args.url:
            parser.error("extract needs --url or --registry")
        print(extract.extract_url(args.url, args.topic, force=args.force) or "unchanged since last extraction — no model call")
        return 0
    if args.command == "validate":
        from . import validate

        return validate.main()
    if args.command == "monitor":
        from . import monitor

        return monitor.main()

    stage = "stage 1" if args.command != "supply" else "stages 1–2 (docs/where-to-buy.md)"
    print(f"[pipeline] '{args.command}' is not implemented yet — see docs/plan.md, {stage}.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
