def _get_pitch_segments(notes):
    if not notes:
        return []

    events = []
    for n in notes:
        events.append((n["start"], "on", n["pitch"]))
        events.append((n["end"], "off", n["pitch"]))

    events.sort(key=lambda x: (x[0], x[1] == "on"))

    segments = []
    current_pitches = set()
    last_time = 0.0

    for t, evt_type, pitch in events:
        dur = t - last_time
        if dur > 0 and current_pitches:
            segments.append((list(current_pitches), dur))

        if evt_type == "on":
            current_pitches.add(pitch)
        else:
            if pitch in current_pitches:
                current_pitches.remove(pitch)

        last_time = t

    return segments
