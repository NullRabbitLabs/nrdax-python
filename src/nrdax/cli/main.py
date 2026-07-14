"""The ``nrdax`` command-line interface.

A thin dispatch layer over the library: every command resolves a data source,
loads an :class:`~nrdax.registry.NRDAX`, and calls library functions. No domain
logic lives here. Errors map to stable exit codes (see
:class:`~nrdax.errors.ExitCode`); with ``--format json`` errors are emitted as a
structured ``{"error": {"code", "message"}}`` body.

Built on ``argparse`` from the standard library so the CLI starts fast and the
package installs with zero runtime dependencies.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import Callable
from typing import Any

from .. import cache as _cache
from .. import changes as _changes
from .. import citations as _citations
from .._version import __version__
from ..citations import CITATION_STYLES
from ..errors import ExitCode, InvalidArgumentError, NrdaxError, ValidationError
from ..exporters import EXPORT_FORMATS, export
from ..queries.search import FIELDS as SEARCH_FIELDS
from ..registry import NRDAX
from ..sources import Source
from ..vocab import (
    DISCOVERY_ORIGINS,
    FAMILIES,
    FIDELITY_CLASSES,
    NRDAX_SCHEMA_VERSION,
    REFERENCE_KINDS,
    REPRODUCTION_STATUSES,
    STATUSES,
)
from . import formatting as fmt

PROG = "nrdax"


# -- source resolution ----------------------------------------------------------


def resolve_source(spec: str | None) -> Source | None:
    """Turn a ``--source`` spec into a :class:`Source` (``None`` = default).

    Accepts ``cache``, ``api`` / ``api:URL``, ``feed:LOCATION``, ``file:PATH``,
    ``stix:PATH``, or a bare path/dir/URL (auto-detected: a directory or feed URL
    loads as a feed, a file loads as a file)."""
    if spec is None:
        return None
    if spec == "cache":
        return _cache.CacheSource()
    if spec == "api" or spec.startswith("api:"):
        from ..sources.api import ApiSource

        _, _, url = spec.partition(":")
        return ApiSource(url) if url else ApiSource()
    if spec.startswith("feed:"):
        from ..sources.feed import FeedSource

        return FeedSource(spec[len("feed:") :])
    if spec.startswith("file:"):
        from ..sources.file import FileSource

        return FileSource(spec[len("file:") :])
    if spec.startswith("stix:"):
        from ..sources.stix import StixSource

        return StixSource(path=spec[len("stix:") :])
    # Bare spec: auto-detect.
    if spec.startswith(("http://", "https://")) or os.path.isdir(spec):
        from ..sources.feed import FeedSource

        return FeedSource(spec)
    from ..sources.file import FileSource

    return FileSource(spec)


def load_registry(args: argparse.Namespace) -> NRDAX:
    source = resolve_source(getattr(args, "source", None))
    return NRDAX.load(source, strict=getattr(args, "strict", False))


# -- output helpers -------------------------------------------------------------


def emit(text: str, output: str | None = None) -> None:
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
    else:
        print(text)


def _predicate_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    """Filter kwargs shared by list/export/changes (only set-ones passed through)."""
    kw: dict[str, Any] = {}
    for name in (
        "family",
        "chain",
        "status",
        "fidelity",
        "discovery_origin",
        "reproduction_status",
        "implementation",
        "reference",
        "text",
    ):
        value = getattr(args, name, None)
        if value is not None:
            kw[name] = value
    if getattr(args, "reference_contains", False):
        kw["reference_contains"] = True
    return kw


# -- command handlers -----------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> int:
    reg = load_registry(args)
    fields = tuple(args.search_fields) if args.search_fields else None
    results = reg.search(args.query, limit=args.limit, fields=fields)
    if args.format == "json":
        emit(fmt.dumps(fmt.search_json(args.query, results)))
    elif args.format == "csv":
        emit(export([r.technique for r in results], "csv", version=reg.version, fields=args.fields))
    else:
        emit(fmt.search_table(results, explain=args.explain))
    return ExitCode.OK


def cmd_get(args: argparse.Namespace) -> int:
    reg = load_registry(args)
    tech = reg.get(args.id)  # raises NotFoundError -> exit 3
    if args.format == "json":
        emit(fmt.dumps(fmt.technique_json(tech)))
    elif args.format == "stix":
        emit(export([tech], "stix", version=reg.version))
    else:
        emit(fmt.technique_detail(tech))
    return ExitCode.OK


def cmd_list(args: argparse.Namespace) -> int:
    reg = load_registry(args)
    techniques = reg.filter(**_predicate_kwargs(args))
    if args.limit is not None:
        techniques = techniques[: args.limit]
    if args.format == "json":
        payload = {
            "registry_version": reg.version,
            "count": len(techniques),
            "techniques": [fmt.technique_json(t) for t in techniques],
        }
        emit(fmt.dumps(payload))
    elif args.format == "csv":
        emit(export(techniques, "csv", version=reg.version, fields=args.fields))
    else:
        emit(fmt.technique_table(techniques, tuple(args.fields) if args.fields else None))
        print(f"\n{len(techniques)} technique(s)", file=sys.stderr)
    return ExitCode.OK


def cmd_related(args: argparse.Namespace) -> int:
    reg = load_registry(args)
    rel = reg.related(args.id)  # raises NotFoundError -> exit 3
    if args.format == "json":
        emit(fmt.dumps(fmt.related_json(rel)))
    else:
        emit(fmt.related_detail(rel))
    return ExitCode.OK


def cmd_export(args: argparse.Namespace) -> int:
    reg = load_registry(args)
    techniques = reg.filter(**_predicate_kwargs(args))
    text = export(
        techniques,
        args.format,
        version=reg.version,
        doi=reg.doi,
        fields=args.fields,
        csv_rows=args.csv_rows,
    )
    emit(text, args.output)
    where = args.output or "stdout"
    print(
        f"exported {len(techniques)} technique(s) as {args.format} to {where}",
        file=sys.stderr,
    )
    return ExitCode.OK


def cmd_cite(args: argparse.Namespace) -> int:
    reg = load_registry(args)
    emit(_citations.cite(reg, args.id, style=args.format, accessed=args.accessed))
    return ExitCode.OK


def cmd_changes(args: argparse.Namespace) -> int:
    if args.from_version or args.to_version:
        raise InvalidArgumentError(
            "comparison by version number is not available: NRDAX does not yet publish "
            "historical versioned releases addressable by version. Diff two snapshots "
            "instead, e.g. --from cache --to api, or --from file:old.jsonl --to file:new.jsonl. "
            "Use --since <date> for techniques added since a date."
        )
    predicate = None
    kw = _predicate_kwargs(args)
    if kw:
        from ..queries.filters import build_predicate

        predicate = build_predicate(**kw)

    if args.since:
        reg = load_registry(args)
        hits = _changes.since(reg, args.since, predicate=predicate)
        if args.format == "json":
            emit(
                fmt.dumps(
                    {
                        "since": args.since,
                        "registry_version": reg.version,
                        "count": len(hits),
                        "techniques": [fmt.technique_json(t) for t in hits],
                    }
                )
            )
        else:
            emit(fmt.technique_table(hits))
            print(f"\n{len(hits)} technique(s) first seen since {args.since}", file=sys.stderr)
        return ExitCode.OK

    if not (args.from_source and args.to_source):
        raise InvalidArgumentError(
            "provide either --since <date>, or both --from <source> and --to <source>"
        )
    old = NRDAX.load(resolve_source(args.from_source), strict=args.strict)
    new = NRDAX.load(resolve_source(args.to_source), strict=args.strict)
    cs = _changes.diff(old, new, predicate=predicate)
    if args.format == "json":
        emit(fmt.dumps(fmt.changes_json(cs)))
    else:
        emit(fmt.changes_detail(cs))
    return ExitCode.OK


def cmd_info(args: argparse.Namespace) -> int:
    reg = load_registry(args)
    cov = reg.coverage
    cache_info = _cache.info()
    src = reg.source_meta
    data: dict[str, Any] = {
        "cli_version": __version__,
        "library_version": __version__,
        "dataset_version": reg.version,
        "doi": reg.doi,
        "schema_version": reg.schema_version,
        "technique_count": len(reg),
        "reproduced_count": sum(1 for t in reg if t.is_reproduced),
        "known_only_count": sum(1 for t in reg if not t.is_reproduced),
        "family_count": len(reg.families_vocab),
        "chain_count": len(cov.chains),
        "source": {
            "kind": src.kind if src else None,
            "location": src.location if src else None,
            "fetched_at": src.fetched_at if src else None,
        },
        "cache": cache_info,
        "validation_issues": len(reg.validate()),
    }
    if args.format == "json":
        emit(fmt.dumps(data))
        return ExitCode.OK

    lines = [
        f"nrdax {PROG} {__version__}  (library {__version__}, schema {reg.schema_version})",
        "",
        f"dataset version    {reg.version}",
        f"doi                {reg.doi or '(not minted)'}",
        f"techniques         {len(reg)}  "
        f"({data['reproduced_count']} reproduced, {data['known_only_count']} known-only)",
        f"families           {data['family_count']}",
        f"chains             {data['chain_count']}",
        f"source             {data['source']['kind']}: {data['source']['location']}",
        f"source fetched at  {data['source']['fetched_at'] or '(local)'}",
        f"validation issues  {data['validation_issues']}",
        "",
        f"cache dir          {cache_info['cache_dir']}",
        f"cache snapshot     {'present' if cache_info['snapshot_present'] else 'none'}",
    ]
    if cache_info.get("snapshot_present"):
        lines.append(
            f"cache version      {cache_info.get('version')} "
            f"(fetched {cache_info.get('fetched_at')})"
        )
    emit("\n".join(lines))
    return ExitCode.OK


def cmd_version(args: argparse.Namespace) -> int:
    if args.format == "json":
        emit(
            fmt.dumps(
                {
                    "cli_version": __version__,
                    "library_version": __version__,
                    "schema_version": NRDAX_SCHEMA_VERSION,
                }
            )
        )
    else:
        emit(f"{PROG} {__version__} (library {__version__}, NRDAX schema {NRDAX_SCHEMA_VERSION})")
    return ExitCode.OK


def cmd_update(args: argparse.Namespace) -> int:
    spec = args.source or "api"  # default remote is the live API
    source = resolve_source(spec)
    if source is None:  # pragma: no cover - defensive
        raise InvalidArgumentError("no update source resolved")
    raw = source.load()
    if args.version and raw.version != args.version:
        raise InvalidArgumentError(
            f"requested version {args.version!r} but source served {raw.version!r}. "
            "The live API serves only the current version; pin a specific version with "
            "--source feed:<url-or-dir> pointing at that release's static feed."
        )
    path = _cache.write_snapshot(raw)
    print(
        f"updated cache: {len(raw.techniques)} technique(s), version {raw.version} "
        f"(from {spec}) -> {path}"
    )
    return ExitCode.OK


def cmd_cache(args: argparse.Namespace) -> int:
    if args.cache_action == "clear":
        removed = _cache.clear()
        print("cache cleared" if removed else "cache was already empty")
        return ExitCode.OK
    # info
    info = _cache.info()
    if args.format == "json":
        emit(fmt.dumps(info))
    else:
        lines = [f"cache dir          {info['cache_dir']}"]
        if info["snapshot_present"]:
            lines += [
                f"snapshot           present ({info.get('size_bytes', 0)} bytes)",
                f"version            {info.get('version')}",
                f"doi                {info.get('doi') or '(not minted)'}",
                f"techniques         {info.get('technique_count')}",
                f"fetched at         {info.get('fetched_at')}",
                f"source             {info.get('source')}",
            ]
        else:
            lines.append("snapshot           none (run 'nrdax update')")
        emit("\n".join(lines))
    return ExitCode.OK


_SCHEMA_NOTE = (
    "The NRDAX feed does not carry a schema_version field; this value is tracked by "
    "nrdax-python. NRDAX has no 'implementation' or 'surface' field and no asserted "
    "technique-to-technique relationships; 'related' and --implementation are derived. "
    "Reproduction status is derived (reproduced iff a technique has an instance)."
)
_TECHNIQUE_FIELDS = [
    "id",
    "name",
    "display_name",
    "mechanism",
    "family",
    "status",
    "first_seen",
    "instances",
    "external_references",
    "provenance_note",
]
_INSTANCE_FIELDS = [
    "chain",
    "primitive_id",
    "bundle_ref",
    "fidelity",
    "discovery_origin",
    "external_references",
]


def cmd_schema(args: argparse.Namespace) -> int:
    if args.format == "json":
        emit(
            fmt.dumps(
                {
                    "schema_version": NRDAX_SCHEMA_VERSION,
                    "note": _SCHEMA_NOTE,
                    "vocabularies": {
                        "families": list(FAMILIES),
                        "statuses": list(STATUSES),
                        "fidelity_classes": list(FIDELITY_CLASSES),
                        "discovery_origins": list(DISCOVERY_ORIGINS),
                        "reference_kinds": list(REFERENCE_KINDS),
                        "reproduction_statuses": list(REPRODUCTION_STATUSES),
                    },
                    "technique_fields": _TECHNIQUE_FIELDS,
                    "instance_fields": _INSTANCE_FIELDS,
                }
            )
        )
        return ExitCode.OK
    lines = [
        f"NRDAX schema version {NRDAX_SCHEMA_VERSION} (tracked by nrdax-python)",
        "",
        "families:          " + ", ".join(FAMILIES),
        "statuses:          " + ", ".join(STATUSES),
        "fidelity classes:  " + ", ".join(FIDELITY_CLASSES),
        "discovery origins: " + ", ".join(DISCOVERY_ORIGINS),
        "reference kinds:   " + ", ".join(REFERENCE_KINDS),
        "",
        "technique fields:  " + ", ".join(_TECHNIQUE_FIELDS),
        "instance fields:   " + ", ".join(_INSTANCE_FIELDS),
        "",
        "note: " + _SCHEMA_NOTE,
    ]
    emit("\n".join(lines))
    return ExitCode.OK


# -- parser construction --------------------------------------------------------


def _add_source_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--source",
        metavar="SPEC",
        help=(
            "data source: cache | api[:URL] | feed:LOCATION | file:PATH | "
            "stix:PATH | a bare path/dir/URL. Default: the cached snapshot from a "
            "prior `nrdax update` (no data is bundled; errors if the cache is empty)."
        ),
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="fail on the first data validation issue instead of loading leniently",
    )


def _add_filter_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--family", choices=FAMILIES, help="exact family")
    p.add_argument("--chain", help="techniques with a reproduced instance on this chain")
    p.add_argument("--status", choices=STATUSES, help="lifecycle status")
    p.add_argument("--fidelity", choices=FIDELITY_CLASSES, help="any instance with this fidelity")
    p.add_argument(
        "--discovery-origin",
        choices=DISCOVERY_ORIGINS,
        dest="discovery_origin",
        help="any instance with this discovery origin",
    )
    p.add_argument(
        "--reproduction-status",
        choices=REPRODUCTION_STATUSES,
        dest="reproduction_status",
        help="reproduced (has an instance) or known (catalogued only)",
    )
    p.add_argument(
        "--implementation",
        help="DERIVED heuristic: match an implementation/client across primitive ids, "
        "mechanism and references (NRDAX has no first-class implementation field)",
    )
    p.add_argument(
        "--reference", help="carries an external reference (advisory/CVE/GHSA) with this id"
    )
    p.add_argument(
        "--reference-contains",
        action="store_true",
        dest="reference_contains",
        help="treat --reference as a substring match",
    )
    p.add_argument("--text", help="free-text match across searchable fields")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Programmatic access to NRDAX - the NullRabbit Decentralised Attack indeX.",
    )
    parser.add_argument("--version", action="version", version=f"{PROG} {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # search
    sp = sub.add_parser("search", help="search techniques (deterministic, offline)")
    _add_source_arg(sp)
    sp.add_argument("query", help="query text (id, name, mechanism, chain, family, reference...)")
    sp.add_argument("--limit", type=int, default=20, help="max results (default 20)")
    sp.add_argument(
        "--search-fields",
        nargs="+",
        choices=SEARCH_FIELDS,
        metavar="FIELD",
        help="restrict which fields are searched",
    )
    sp.add_argument("--explain", action="store_true", help="show which fields matched")
    sp.add_argument("--fields", nargs="+", metavar="FIELD", help="columns for --format csv")
    sp.add_argument("--format", choices=("table", "json", "csv"), default="table")
    sp.set_defaults(func=cmd_search)

    # get
    gp = sub.add_parser("get", help="retrieve one technique by id")
    _add_source_arg(gp)
    gp.add_argument("id", help="technique id, e.g. NRDAX-T0006")
    gp.add_argument("--format", choices=("table", "json", "stix"), default="table")
    gp.set_defaults(func=cmd_get)

    # list
    lp = sub.add_parser("list", help="list/filter techniques")
    _add_source_arg(lp)
    _add_filter_args(lp)
    lp.add_argument("--limit", type=int, help="max techniques")
    lp.add_argument("--fields", nargs="+", metavar="FIELD", help="columns (table/csv)")
    lp.add_argument("--format", choices=("table", "json", "csv"), default="table")
    lp.set_defaults(func=cmd_list)

    # related
    rp = sub.add_parser("related", help="derived relationships for a technique")
    _add_source_arg(rp)
    rp.add_argument("id", help="technique id")
    rp.add_argument("--format", choices=("table", "json"), default="table")
    rp.set_defaults(func=cmd_related)

    # export
    ep = sub.add_parser("export", help="export techniques (json/csv/stix)")
    _add_source_arg(ep)
    _add_filter_args(ep)
    ep.add_argument("--format", choices=EXPORT_FORMATS, default="json")
    ep.add_argument("--fields", nargs="+", metavar="FIELD", help="fields for json/csv projection")
    ep.add_argument(
        "--csv-rows",
        choices=("techniques", "instances"),
        default="techniques",
        dest="csv_rows",
        help="CSV row granularity",
    )
    ep.add_argument("--output", "-o", help="write to this file instead of stdout")
    ep.set_defaults(func=cmd_export)

    # cite
    cp = sub.add_parser("cite", help="generate a citation")
    _add_source_arg(cp)
    cp.add_argument("id", help="technique id")
    cp.add_argument("--format", choices=CITATION_STYLES, default="text")
    cp.add_argument("--accessed", help="access date YYYY-MM-DD (default: today)")
    cp.set_defaults(func=cmd_cite)

    # changes
    chp = sub.add_parser("changes", help="inspect changes (since a date, or between two sources)")
    _add_source_arg(chp)
    _add_filter_args(chp)
    chp.add_argument("--since", metavar="DATE", help="techniques first seen on/after DATE")
    chp.add_argument("--from", dest="from_source", metavar="SOURCE", help="baseline source spec")
    chp.add_argument("--to", dest="to_source", metavar="SOURCE", help="comparison source spec")
    chp.add_argument("--from-version", dest="from_version", help="(unsupported - see help)")
    chp.add_argument("--to-version", dest="to_version", help="(unsupported - see help)")
    chp.add_argument("--format", choices=("table", "json"), default="table")
    chp.set_defaults(func=cmd_changes)

    # info
    ip = sub.add_parser("info", help="dataset, source, and cache information")
    _add_source_arg(ip)
    ip.add_argument("--format", choices=("text", "json"), default="text")
    ip.set_defaults(func=cmd_info)

    # version
    vp = sub.add_parser("version", help="CLI, library, and schema versions")
    vp.add_argument("--format", choices=("text", "json"), default="text")
    vp.set_defaults(func=cmd_version)

    # update
    up = sub.add_parser("update", help="fetch the latest dataset into the local cache")
    up.add_argument("--source", metavar="SPEC", help="source to fetch from (default: api)")
    up.add_argument("--version", help="require this dataset version (else error)")
    up.set_defaults(func=cmd_update)

    # cache
    cap = sub.add_parser("cache", help="inspect or clear the local cache")
    cap.add_argument("cache_action", choices=("info", "clear"), help="cache action")
    cap.add_argument("--format", choices=("text", "json"), default="text")
    cap.set_defaults(func=cmd_cache)

    # schema
    scp = sub.add_parser("schema", help="show the NRDAX schema vocabularies and fields")
    scp.add_argument("--format", choices=("text", "json"), default="text")
    scp.set_defaults(func=cmd_schema)

    return parser


def _error_out(err: NrdaxError, args: argparse.Namespace | None) -> int:
    as_json = getattr(args, "format", None) == "json" if args else False
    if isinstance(err, ValidationError):
        message = str(err)
    else:
        message = str(err)
    if as_json:
        print(fmt.dumps({"error": {"code": err.code, "message": message}}))
    else:
        print(f"{PROG}: error: {message}", file=sys.stderr)
    return int(err.exit_code)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace], int] = args.func
    try:
        return handler(args)
    except NrdaxError as err:
        return _error_out(err, args)
    except BrokenPipeError:  # pragma: no cover - piping to head/less
        with contextlib.suppress(OSError):
            sys.stdout.close()
        return int(ExitCode.OK)
    except KeyboardInterrupt:  # pragma: no cover
        print(f"\n{PROG}: interrupted", file=sys.stderr)
        return int(ExitCode.ERROR)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
