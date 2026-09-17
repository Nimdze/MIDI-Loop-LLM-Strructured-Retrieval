"""High-level preprocessing pipeline for a folder of MIDI files."""

import logging
from collections.abc import Callable
from pathlib import Path

from midi_preprocessor.slicer import slice_midi
from midi_preprocessor.splitter import split_instruments
from midi_preprocessor.tempo_normalizer import normalize_tempo
from midi_preprocessor.validators import validate_midis

logger = logging.getLogger(__name__)


def _walk_midi_files(folder: Path) -> list[Path]:
    files = []
    for path in folder.rglob("*"):
        if path.suffix.lower() not in {".mid", ".midi"}:
            continue
        if path.name.startswith("._"):
            continue
        if "__MACOSX" in path.parts:
            continue
        files.append(path)
    return sorted(files)


Callback = Callable[[str], None]


def process_folder(
    input_folder: Path,
    output_folder: Path,
    target_bpm: float | None = None,
    slice_bars: int | None = None,
    no_split: bool = False,
    progress: Callback | None = None,
) -> dict[str, int]:
    """Preprocess all MIDI files in a folder and write the cleaned output.

    Returns a dict with the number of processed, skipped, and failed files.
    A file is counted as failed if any preprocessing step fails; processing
    continues with the next file.
    """
    notify = progress or (lambda _msg: None)
    output_folder.mkdir(parents=True, exist_ok=True)

    valid_files, invalid_files = validate_midis(input_folder)

    processed = 0
    failed = 0
    for file_path in valid_files:
        try:
            relative = file_path.relative_to(input_folder)
            rel_no_ext = relative.with_suffix("")
            file_output_folder = output_folder / rel_no_ext.parent

            if not no_split:
                split_files = split_instruments(
                    file_path,
                    file_output_folder,
                    prefix=relative.stem,
                )
            else:
                split_files = [file_path]

            for split_file in split_files:
                stem = split_file.stem

                if target_bpm:
                    normalized_path = file_output_folder / f"{stem}_bpm{target_bpm}.mid"
                    normalize_tempo(split_file, normalized_path, target_bpm=target_bpm)
                    working_file = normalized_path
                else:
                    working_file = split_file

                if slice_bars:
                    slice_midi(
                        working_file,
                        file_output_folder / f"{stem}_slices",
                        slice_bars=slice_bars,
                        prefix=stem,
                    )

            processed += 1
            notify(f"Processed {relative}")
        except Exception as e:
            logger.warning("Failed to process %s: %s", file_path, e, exc_info=True)
            failed += 1
            notify(f"Failed {file_path}")

    return {"processed": processed, "skipped": len(invalid_files), "failed": failed}


__all__ = ["process_folder", "_walk_midi_files"]
