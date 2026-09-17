import argparse
import json
import logging
from pathlib import Path

from midi_analyzer_tagger.analysis import (
    ExtractorRegistry,
    MidiData,
    Pipeline,
    configure_logging,
)
from midi_analyzer_tagger.exporters import TaxonomyExporter
from midi_analyzer_tagger.extractors import PLUGINS
from midi_analyzer_tagger.storage import AnalysisDatabase

logger = logging.getLogger(__name__)

MIDI_EXTENSIONS = {".mid", ".midi"}
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # MIDI_RETRIEVE/
_CANONICAL_TAXONOMY = _PROJECT_ROOT / "taxonomy.json"


def _is_midi_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in MIDI_EXTENSIONS


def _should_skip_resource_fork(path: Path) -> bool:
    return path.name.startswith("._") or "__MACOSX" in path.parts


def _walk_midi_files(folder: Path) -> list[Path]:
    files = []
    for path in folder.rglob("*"):
        if _should_skip_resource_fork(path):
            continue
        if _is_midi_file(path):
            files.append(path)
    return sorted(files)


def _load_existing_taxonomy(taxonomy_path: Path) -> dict:
    if not taxonomy_path.exists():
        return {}
    try:
        return json.loads(taxonomy_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def analyze_file(
    path: Path,
    db_path: Path,
    taxonomy_path: Path,
):
    """Analyze a single MIDI file and store the result."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    taxonomy_path.parent.mkdir(parents=True, exist_ok=True)

    existing_taxonomy = _load_existing_taxonomy(taxonomy_path)

    midi = MidiData.from_path(path)
    registry = ExtractorRegistry(PLUGINS, existing_taxonomy=existing_taxonomy)
    registry.compile_taxonomy()
    pipeline = Pipeline(registry)
    payload = pipeline.analyze(midi)
    payload.metadata["path"] = str(path)

    with AnalysisDatabase(db_path) as db:
        db.store(path, payload)
    TaxonomyExporter(registry).to_json(taxonomy_path)
    TaxonomyExporter(registry).to_json(_CANONICAL_TAXONOMY)
    return payload


def analyze_command(args: argparse.Namespace) -> int:
    configure_logging()

    path = Path(args.path)
    if not path.exists():
        logger.error("File not found: %s", path)
        return 1

    db_path = Path(args.db)
    taxonomy_path = Path(args.taxonomy_json)

    payload = analyze_file(path, db_path, taxonomy_path)

    logger.info("Analyzed: %s", path)
    logger.info("Database written to: %s", db_path)
    logger.info("Taxonomy written to: %s", taxonomy_path)

    print(json.dumps(payload.to_dict(), indent=2))
    return 0


def analyze_folder(
    input_folder: Path,
    output_folder: Path,
    db_path: Path | None = None,
    taxonomy_path: Path | None = None,
    force: bool = False,
) -> dict[str, int]:
    """Analyze all MIDI files in a folder and store the results."""
    if not input_folder.exists() or not input_folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {input_folder}")

    output_folder.mkdir(parents=True, exist_ok=True)

    db_path = db_path or output_folder / "analysis.db"
    taxonomy_path = taxonomy_path or output_folder / "taxonomy.json"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    taxonomy_path.parent.mkdir(parents=True, exist_ok=True)

    existing_taxonomy = _load_existing_taxonomy(taxonomy_path)

    registry = ExtractorRegistry(PLUGINS, existing_taxonomy=existing_taxonomy)
    registry.compile_taxonomy()
    pipeline = Pipeline(registry)

    existing_files = set()
    with AnalysisDatabase(db_path) as db:
        rows = db.connection.execute("SELECT path FROM files").fetchall()
        existing_files = {row["path"] for row in rows}

    midi_files = _walk_midi_files(input_folder)

    processed = 0
    skipped = 0
    failed = 0

    with AnalysisDatabase(db_path) as db:
        for file_path in midi_files:
            relative_path = file_path.relative_to(input_folder)

            if str(relative_path) in existing_files and not force:
                logger.info("Skipping (already analyzed): %s", relative_path)
                skipped += 1
                continue

            try:
                midi = MidiData.from_path(file_path)
                payload = pipeline.analyze(midi)
                db.store(relative_path, payload)
                logger.info("Analyzed [%s]: %s", payload.family, relative_path)
                processed += 1
            except Exception as e:
                logger.error("Failed to analyze %s: %s", relative_path, e)
                failed += 1

    TaxonomyExporter(registry).to_json(taxonomy_path)
    TaxonomyExporter(registry).to_json(_CANONICAL_TAXONOMY)

    return {
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "total": len(midi_files),
    }


def analyze_folder_command(args: argparse.Namespace) -> int:
    configure_logging()

    result = analyze_folder(
        Path(args.input_folder),
        Path(args.output),
        db_path=Path(args.db) if args.db else None,
        taxonomy_path=Path(args.taxonomy_json) if args.taxonomy_json else None,
        force=args.force,
    )

    logger.info(
        "Done. processed=%d skipped=%d failed=%d total=%d",
        result["processed"],
        result["skipped"],
        result["failed"],
        result["total"],
    )

    print(
        f"Done. analyzed: {result['processed']}, skipped: {result['skipped']}, "
        f"failed: {result['failed']}, total MIDI files: {result['total']}"
    )
    print(f"Database written to: {args.db or Path(args.output) / 'analysis.db'}")
    print(f"Taxonomy written to: {args.taxonomy_json or Path(args.output) / 'taxonomy.json'}")
    return 0 if result["failed"] == 0 else 0 if args.ignore_failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="midi-analyzer-tagger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a single MIDI file")
    analyze.add_argument("path", help="Path to MIDI file")
    analyze.add_argument(
        "--db",
        default="analysis.db",
        help="Path to SQLite database",
    )
    analyze.add_argument(
        "--taxonomy-json",
        default="taxonomy.json",
        help="Path to taxonomy JSON output",
    )
    analyze.set_defaults(func=analyze_command)

    analyze_folder = subparsers.add_parser("analyze-folder", help="Analyze all MIDI files in a folder recursively")
    analyze_folder.add_argument("input_folder", help="Root folder containing MIDI files")
    analyze_folder.add_argument(
        "--output",
        default=".",
        help="Output folder for database and taxonomy (default: current directory)",
    )
    analyze_folder.add_argument(
        "--db",
        default=None,
        help="Override path for SQLite database (default: <output>/analysis.db)",
    )
    analyze_folder.add_argument(
        "--taxonomy-json",
        default=None,
        help="Override path for taxonomy JSON output (default: <output>/taxonomy.json)",
    )
    analyze_folder.add_argument(
        "--force",
        action="store_true",
        help="Re-analyze files already present in the database",
    )
    analyze_folder.add_argument(
        "--ignore-failures",
        action="store_true",
        help="Return success even if some files failed",
    )
    analyze_folder.set_defaults(func=analyze_folder_command)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
