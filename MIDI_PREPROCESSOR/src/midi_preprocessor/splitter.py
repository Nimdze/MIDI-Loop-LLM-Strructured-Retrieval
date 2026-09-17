import logging
from pathlib import Path

import pretty_midi

logger = logging.getLogger(__name__)


def _sanitize_name(name: str) -> str:
    """Turn a string into a safe filename component."""
    replacements = {
        "/": "_",
        "\\": "_",
        ":": "_",
        "*": "_",
        "?": "_",
        '"': "_",
        "<": "_",
        ">": "_",
        "|": "_",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()


def _instrument_name(instrument: pretty_midi.Instrument) -> str:
    """Generate a human-readable name for an instrument."""
    if instrument.is_drum:
        return "Drums"

    program = instrument.program
    name = pretty_midi.program_to_instrument_name(program)
    return name or f"Program_{program}"


def split_instruments(
    input_path: Path,
    output_folder: Path,
    prefix: str | None = None,
) -> list[Path]:
    """
    Split a multi-instrument MIDI file into one file per instrument.

    Args:
        input_path: Path to source MIDI file.
        output_folder: Folder where split files will be written.
        prefix: Optional filename prefix. Defaults to source file stem.

    Returns:
        List of written output paths.
    """
    input_path = Path(input_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    midi = pretty_midi.PrettyMIDI(str(input_path))
    base_name = prefix if prefix else input_path.stem

    _, tempos = midi.get_tempo_changes()
    initial_tempo = float(tempos[0]) if tempos is not None and len(tempos) > 0 else 120.0

    written = []
    for i, instrument in enumerate(midi.instruments):
        single_midi = pretty_midi.PrettyMIDI(initial_tempo=initial_tempo)
        new_instrument = pretty_midi.Instrument(
            program=instrument.program,
            is_drum=instrument.is_drum,
            name=instrument.name,
        )
        new_instrument.notes = list(instrument.notes)
        new_instrument.pitch_bends = list(instrument.pitch_bends)
        new_instrument.control_changes = list(instrument.control_changes)
        single_midi.instruments.append(new_instrument)
        single_midi.time_signature_changes = list(midi.time_signature_changes)
        single_midi.key_signature_changes = list(midi.key_signature_changes)
        single_midi.lyrics = list(midi.lyrics)
        single_midi.text_events = list(midi.text_events)

        suffix = _sanitize_name(_instrument_name(instrument))
        out_name = f"{base_name}_{suffix}.mid"
        out_path = output_folder / out_name

        # Avoid collisions if multiple instruments have the same name
        counter = 1
        while out_path.exists():
            out_name = f"{base_name}_{suffix}_{counter}.mid"
            out_path = output_folder / out_name
            counter += 1

        single_midi.write(str(out_path))
        written.append(out_path)
        logger.info("Wrote: %s", out_path.name)

    return written
