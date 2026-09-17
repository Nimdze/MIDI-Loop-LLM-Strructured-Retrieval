import argparse
import logging
from pathlib import Path

from midi_preprocessor.processor import process_folder

logger = logging.getLogger(__name__)


def _configure_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def process_command(args: argparse.Namespace) -> int:
    _configure_logging()
    result = process_folder(
        Path(args.input_folder),
        Path(args.output),
        target_bpm=args.target_bpm,
        slice_bars=args.slice_bars,
        no_split=args.no_split,
    )

    if result["skipped"]:
        logger.warning("%d invalid files skipped", result["skipped"])
    if result.get("failed"):
        logger.warning("%d files failed during processing", result["failed"])

    logger.info(
        "Done. Processed %d files, skipped %d, failed %d.",
        result["processed"],
        result["skipped"],
        result.get("failed", 0),
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="midi-preprocessor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", help="Process a folder of MIDI files")
    process.add_argument("input_folder", help="Folder of MIDI files to preprocess")
    process.add_argument(
        "--output",
        default="./clean",
        help="Output folder for processed MIDI files",
    )
    process.add_argument(
        "--target-bpm",
        type=float,
        default=None,
        help="Normalize all files to this BPM",
    )
    process.add_argument(
        "--slice-bars",
        type=int,
        default=None,
        help="Slice files into segments of this many bars",
    )
    process.add_argument(
        "--no-split",
        action="store_true",
        help="Do not split files by instrument",
    )

    args = parser.parse_args(argv)
    if args.command == "process":
        return process_command(args)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
