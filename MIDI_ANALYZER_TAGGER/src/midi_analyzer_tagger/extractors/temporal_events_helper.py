import os
from typing import Any


def _note_attr(note: Any, attr: str) -> Any:
    if isinstance(note, dict):
        return note[attr]
    return getattr(note, attr)


def get_bps(midi) -> float:
    if "TARGET_BPM" in os.environ:
        return float(os.environ["TARGET_BPM"]) / 60.0
    times, tempi = midi.get_tempo_changes()
    if len(tempi) > 0 and tempi[0] > 0:
        return float(tempi[0]) / 60.0
    return 120.0 / 60.0


def group_notes_into_events(notes: list[Any], bps: float, threshold: float = 0.05) -> list[list[Any]]:
    if not notes:
        return []

    sorted_notes = sorted(notes, key=lambda n: _note_attr(n, "start"))
    events = []
    current_group = [sorted_notes[0]]
    current_start = _note_attr(sorted_notes[0], "start") * bps
    current_end = _note_attr(sorted_notes[0], "end") * bps

    for note in sorted_notes[1:]:
        start = _note_attr(note, "start") * bps
        end = _note_attr(note, "end") * bps
        gap = start - current_start

        if gap <= threshold and start < (current_end - 0.005):
            current_group.append(note)
            if end > current_end:
                current_end = end
        else:
            events.append(current_group)
            current_group = [note]
            current_start = start
            current_end = end

    events.append(current_group)
    return events
