import logging
from pathlib import Path

import pretty_midi

logger = logging.getLogger(__name__)


def get_original_tempo(midi: pretty_midi.PrettyMIDI) -> float:
    """Return the first explicit tempo, or estimate from notes, or fallback to 120."""
    tempo_changes = midi.get_tempo_changes()

    # pretty_midi.get_tempo_changes returns (times, tempos)
    if tempo_changes and len(tempo_changes) >= 2:
        times, tempos = tempo_changes
        if len(tempos) > 0:
            return float(tempos[0])

    try:
        return float(midi.estimate_tempo())
    except ValueError:
        return 120.0


def _scale_event_times(midi: pretty_midi.PrettyMIDI, ratio: float) -> None:
    """Scale the timing of every note-level event in place."""
    for instrument in midi.instruments:
        for note in instrument.notes:
            note.start *= ratio
            note.end *= ratio
        for event in instrument.pitch_bends:
            event.time *= ratio
        for event in instrument.control_changes:
            event.time *= ratio
    for event in midi.time_signature_changes:
        event.time *= ratio
    for event in midi.key_signature_changes:
        event.time *= ratio
    for event in midi.lyrics:
        event.time *= ratio
    for event in midi.text_events:
        event.time *= ratio


def normalize_tempo(
    input_path: Path,
    output_path: Path,
    target_bpm: float = 120.0,
) -> Path:
    """
    Stretch a MIDI file in time so its tempo equals target_bpm.

    Args:
        input_path: Path to source MIDI file.
        output_path: Path to write normalized MIDI file.
        target_bpm: Target tempo in beats per minute.

    Returns:
        Path to the written file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    midi = pretty_midi.PrettyMIDI(str(input_path))
    original_tempo = get_original_tempo(midi)

    if original_tempo != target_bpm:
        _scale_event_times(midi, original_tempo / target_bpm)

    normalized = pretty_midi.PrettyMIDI(initial_tempo=target_bpm)
    normalized.time_signature_changes = list(midi.time_signature_changes)
    normalized.key_signature_changes = list(midi.key_signature_changes)
    normalized.lyrics = list(midi.lyrics)
    normalized.text_events = list(midi.text_events)
    for instrument in midi.instruments:
        normalized.instruments.append(instrument)

    normalized.write(str(output_path))

    if original_tempo == target_bpm:
        logger.info("No tempo change needed for %s", input_path.name)
    else:
        logger.info(
            "Normalized %s: %.1f BPM -> %.1f BPM (ratio %.4f)",
            input_path.name,
            original_tempo,
            target_bpm,
            original_tempo / target_bpm,
        )
    return output_path
