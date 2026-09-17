import logging
from pathlib import Path

import pretty_midi

logger = logging.getLogger(__name__)


def validate_midi_file(file_path: Path) -> tuple[bool, str | None]:
    """
    Validate that a file is a readable MIDI file with at least one note.
    Returns (is_valid, error_message).
    """
    path = Path(file_path)

    if not path.exists():
        return False, "File not found"
    if not path.is_file():
        return False, "Not a file"
    if path.suffix.lower() not in {".mid", ".midi"}:
        return False, f"Unsupported extension: {path.suffix}"

    try:
        midi = pretty_midi.PrettyMIDI(str(path))
    except Exception as e:
        return False, f"Failed to parse MIDI: {e}"

    if not midi.instruments:
        return False, "No instruments"

    total_notes = sum(len(inst.notes) for inst in midi.instruments)
    if total_notes == 0:
        return False, "No notes"

    return True, None


def validate_midis(folder: Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    """
    Validate all MIDI files in a folder recursively.
    Returns (valid_files, invalid_files_with_reasons).
    """
    valid = []
    invalid = []

    for path in sorted(folder.rglob("*")):
        if path.suffix.lower() not in {".mid", ".midi"}:
            continue
        if path.name.startswith("._"):
            continue

        is_valid, error = validate_midi_file(path)
        if is_valid:
            valid.append(path)
            logger.info("Valid: %s", path.relative_to(folder))
        else:
            invalid.append((path, error or "Unknown error"))
            logger.warning("Invalid: %s — %s", path.relative_to(folder), error)

    return valid, invalid
