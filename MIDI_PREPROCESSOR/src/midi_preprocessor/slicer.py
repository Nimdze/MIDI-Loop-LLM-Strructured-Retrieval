import logging
from pathlib import Path

import pretty_midi

logger = logging.getLogger(__name__)


def _in_window(event, start_time: float, end_time: float) -> bool:
    return start_time <= event.time < end_time


def slice_midi(
    input_path: Path,
    output_folder: Path,
    slice_bars: int = 8,
    beats_per_bar: int | None = None,
    prefix: str | None = None,
) -> list[Path]:
    """
    Slice a MIDI file into fixed-bar segments.

    Args:
        input_path: Path to source MIDI file.
        output_folder: Folder where sliced files will be written.
        slice_bars: Length of each slice in bars.
        beats_per_bar: Time signature denominator, default 4/4.
        prefix: Optional filename prefix. Defaults to source file stem.

    Returns:
        List of written output paths.
    """
    input_path = Path(input_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    midi = pretty_midi.PrettyMIDI(str(input_path))
    base_name = prefix if prefix else input_path.stem

    duration = midi.get_end_time()
    tempo = 120.0
    tempo_changes = midi.get_tempo_changes()
    if tempo_changes and len(tempo_changes[1]) > 0:
        tempo = float(tempo_changes[1][0])

    ts = midi.time_signature_changes[0] if midi.time_signature_changes else None
    beats_per_bar = beats_per_bar if beats_per_bar is not None else (ts.numerator if ts else 4)

    seconds_per_beat = 60.0 / tempo
    seconds_per_slice = slice_bars * beats_per_bar * seconds_per_beat

    written = []
    if duration <= seconds_per_slice:
        out_path = output_folder / f"{base_name}_slice001.mid"
        midi.write(str(out_path))
        written.append(out_path)
        logger.info("File shorter than slice length, kept whole: %s", out_path.name)
        return written

    num_slices = int(duration // seconds_per_slice)

    for i in range(num_slices):
        start_time = i * seconds_per_slice
        end_time = (i + 1) * seconds_per_slice

        sliced_midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
        if ts:
            sliced_midi.time_signature_changes = [ts]
        sliced_midi.key_signature_changes = list(midi.key_signature_changes)
        sliced_midi.lyrics = [
            pretty_midi.Lyric(text=lyric.text, time=lyric.time - start_time)
            for lyric in midi.lyrics
            if _in_window(lyric, start_time, end_time)
        ]
        sliced_midi.text_events = [
            pretty_midi.Text(text=text.text, time=text.time - start_time)
            for text in midi.text_events
            if _in_window(text, start_time, end_time)
        ]

        for instrument in midi.instruments:
            new_instrument = pretty_midi.Instrument(
                program=instrument.program,
                is_drum=instrument.is_drum,
                name=instrument.name,
            )

            for note in instrument.notes:
                if note.end <= start_time or note.start >= end_time:
                    continue

                new_note = pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=note.pitch,
                    start=max(0.0, note.start - start_time),
                    end=min(end_time - start_time, note.end - start_time),
                )
                new_instrument.notes.append(new_note)

            for pitch_bend in instrument.pitch_bends:
                if _in_window(pitch_bend, start_time, end_time):
                    new_instrument.pitch_bends.append(
                        pretty_midi.PitchBend(
                            pitch=pitch_bend.pitch,
                            time=pitch_bend.time - start_time,
                        )
                    )

            for control_change in instrument.control_changes:
                if _in_window(control_change, start_time, end_time):
                    new_instrument.control_changes.append(
                        pretty_midi.ControlChange(
                            number=control_change.number,
                            value=control_change.value,
                            time=control_change.time - start_time,
                        )
                    )

            if new_instrument.notes or new_instrument.pitch_bends or new_instrument.control_changes:
                sliced_midi.instruments.append(new_instrument)

        out_path = output_folder / f"{base_name}_slice{i + 1:03d}.mid"
        sliced_midi.write(str(out_path))
        written.append(out_path)
        logger.info("Wrote slice: %s", out_path.name)

    return written
