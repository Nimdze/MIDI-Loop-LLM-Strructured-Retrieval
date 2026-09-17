"""Continuous mixtape generation by concatenating filtered MIDI files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pretty_midi

from midi_exploration.utils import resolve_midi_path


def _make_instrument_key(inst: pretty_midi.Instrument) -> tuple[int, bool, str]:
    return (inst.program, inst.is_drum, inst.name)


def generate_mixtape(
    matrix: pd.DataFrame | None,
    midi_root: Path | None,
    destination: Path,
    export_name: str,
) -> dict[str, Any]:
    """Concatenate all filtered MIDI files into a single continuous loop.

    Returns a dict with the output path, the number of included files, and the
    number of skipped files.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / f"{export_name}_mixtape.mid"

    if matrix is None or matrix.empty:
        return {
            "output_path": None,
            "included": 0,
            "skipped": 0,
        }

    if "path" not in matrix.columns:
        raise ValueError("Mixtape generation requires a 'path' column in the matrix")

    combined = pretty_midi.PrettyMIDI()
    instrument_map: dict[tuple[int, bool, str], pretty_midi.Instrument] = {}

    current_offset = 0.0
    included = 0
    skipped = 0

    for stored_path in matrix["path"]:
        source = resolve_midi_path(stored_path, midi_root)
        if source is None or not source.exists():
            skipped += 1
            continue

        try:
            midi = pretty_midi.PrettyMIDI(str(source))
        except Exception:
            skipped += 1
            continue

        end_time = midi.get_end_time()
        if end_time == 0:
            skipped += 1
            continue

        for instrument in midi.instruments:
            key = _make_instrument_key(instrument)
            if key not in instrument_map:
                combined_inst = pretty_midi.Instrument(
                    program=instrument.program,
                    is_drum=instrument.is_drum,
                    name=instrument.name,
                )
                combined.instruments.append(combined_inst)
                instrument_map[key] = combined_inst
            else:
                combined_inst = instrument_map[key]

            for note in instrument.notes:
                combined_inst.notes.append(
                    pretty_midi.Note(
                        velocity=note.velocity,
                        pitch=note.pitch,
                        start=note.start + current_offset,
                        end=note.end + current_offset,
                    )
                )
            for pitch_bend in instrument.pitch_bends:
                combined_inst.pitch_bends.append(
                    pretty_midi.PitchBend(
                        pitch=pitch_bend.pitch,
                        time=pitch_bend.time + current_offset,
                    )
                )
            for control_change in instrument.control_changes:
                combined_inst.control_changes.append(
                    pretty_midi.ControlChange(
                        number=control_change.number,
                        value=control_change.value,
                        time=control_change.time + current_offset,
                    )
                )

        current_offset += end_time
        included += 1

    if included == 0:
        return {
            "output_path": None,
            "included": 0,
            "skipped": skipped,
        }

    combined.write(str(output_path))
    return {
        "output_path": output_path,
        "included": included,
        "skipped": skipped,
    }


__all__ = ["generate_mixtape"]
