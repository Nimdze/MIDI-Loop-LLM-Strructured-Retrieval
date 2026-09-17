from pathlib import Path

import pretty_midi


class MidiData:
    """Lightweight wrapper around a loaded MIDI file."""

    def __init__(self, midi: pretty_midi.PrettyMIDI, family: str | None = None):
        self.midi = midi
        self.duration = max(0.0, midi.get_end_time())
        self.notes = self._collect_notes()
        self.family = family or self._detect_family()

    @classmethod
    def from_path(cls, path: str | Path, family: str | None = None) -> "MidiData":
        midi = pretty_midi.PrettyMIDI(str(path))
        return cls(midi, family=family)

    def _collect_notes(self) -> list[dict]:
        notes = []
        for instrument in self.midi.instruments:
            for note in instrument.notes:
                notes.append(
                    {
                        "pitch": note.pitch,
                        "start": note.start,
                        "end": note.end,
                        "velocity": note.velocity,
                        "is_drum": instrument.is_drum,
                    }
                )
        return notes

    def _detect_family(self) -> str:
        if any(note["is_drum"] for note in self.notes):
            return "drums"
        return "pitched"
