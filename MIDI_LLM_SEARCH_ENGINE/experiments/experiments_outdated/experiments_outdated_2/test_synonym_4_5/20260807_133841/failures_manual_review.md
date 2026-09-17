# test_4_5 — failures for manual review

Presence (concept) failures: 22 | genuine direction flips: 4

## Presence failures (model did not return all expected concepts)
### 1. [drums/single]
**query:** toms: gaps of rest are large
- expected: `['drum_toms_others_spacing_max_silence_beats']`
- returned: `['drum_toms_others_spacing_long_profile']`

### 2. [drums/combo]
**query:** Kick 2 appears often, two beats per measure in half notes
- expected: `['drum_prevalence_kick_kick_2', 'metadata_time_sig_num', 'metadata_time_sig_den']`
- returned: `['drum_prevalence_kick_kick_2', 'drum_kick_spacing_half_share']`

### 3. [drums/combo]
**query:** High Tom is used throughout, a drum kit
- expected: `['drum_prevalence_toms_others_high_tom', 'metadata_instrument_family']`
- returned: `['drum_prevalence_toms_others_high_tom', 'drum_toms_others_rhythmic_density_bar_to_bar_evolution']`

### 4. [drums/combo]
**query:** toms: no whole-note gaps between attacks, two beats per measure in half notes
- expected: `['drum_toms_others_spacing_whole_share', 'metadata_time_sig_num', 'metadata_time_sig_den']`
- returned: `['drum_toms_others_spacing_half_share', 'drum_toms_others_spacing_whole_share']`

### 5. [drums/combo]
**query:** hats/cymbals: the timing is very tight and locked, hats/cymbals: attacks every half note creating an open feel, toms: tight continuous sound with no real silence, toms: no whole-note gaps between attacks, a drum kit
- expected: `['drum_hats_cymbals_groove_macro_jitter', 'drum_hats_cymbals_spacing_half_share', 'drum_toms_others_spacing_max_silence_beats', 'drum_toms_others_spacing_whole_share', 'metadata_instrument_family']`
- returned: `['drum_hats_cymbals_groove_macro_jitter', 'drum_hats_cymbals_spacing_half_share', 'drum_toms_others_spacing_max_silence_beats', 'drum_toms_others_spacing_whole_share']`

### 6. [drums/combo]
**query:** hats/cymbals: very quiet and gentle throughout, hats/cymbals: quarter note attack feel, snare/clap: no thirty-second-note spacing between attacks, toms: attacks land on every eighth note, a drum kit
- expected: `['drum_hats_cymbals_dynamics_average_velocity', 'drum_hats_cymbals_spacing_quarter_share', 'drum_snare_clap_spacing_32nd_share', 'drum_toms_others_spacing_8th_share', 'metadata_instrument_family']`
- returned: `['drum_hats_cymbals_dynamics_average_velocity', 'drum_hats_cymbals_spacing_quarter_share', 'drum_snare_clap_spacing_32nd_share', 'drum_toms_others_spacing_8th_share']`

### 7. [drums/combo]
**query:** hats/cymbals: very quiet and gentle throughout, claps are a defining textural element, toms: the odd-bar downbeat is rarely played but tight when played, toms: density rises toward the end, a drum kit
- expected: `['drum_hats_cymbals_dynamics_average_velocity', 'drum_prevalence_snare_clap_clap', 'drum_toms_others_grid_attempt_pct_odd1', 'drum_toms_others_grid_success_pct_odd1', 'drum_toms_others_rhythmic_density_trend', 'metadata_instrument_family']`
- returned: `['drum_hats_cymbals_dynamics_average_velocity', 'drum_prevalence_snare_clap_clap', 'drum_toms_others_grid_attempt_pct_odd1', 'drum_toms_others_grid_success_pct_odd1', 'drum_toms_others_rhythmic_density_trend']`

### 8. [pitched/single]
**query:** every note in the loop is brief
- expected: `['duration_max_length_beats']`
- returned: `['duration_short_profile']`

### 9. [pitched/single]
**query:** the notes are spread far apart
- expected: `['texture_avg_wide_gaps_per_burst']`
- returned: `['spacing_long_profile', 'register_spread_semitones']`

### 10. [pitched/single]
**query:** the chords are short and punchy
- expected: `['texture_polyphonic_burst_mean_duration_beats']`
- returned: `['duration_short_profile', 'dynamics_accents_presence', 'texture_polyphonic_pct']`

### 11. [pitched/single]
**query:** a plain diatonic set of pitches
- expected: `['tonality_unique_pitches_count']`
- returned: `['tonality_out_of_key_notes']`

### 12. [pitched/combo]
**query:** the harmony is built mostly on eleventh intervals, the material is mostly monophonic
- expected: `['profile_harmonic_intervals_pct_17_semitones', 'texture_polyphonic_pct']`
- returned: `['profile_harmonic_intervals_pct_17_semitones', 'texture_pct_1_notes']`

### 13. [pitched/combo]
**query:** the harmony is dense rather than open, the tonic pitch and mode are stated
- expected: `['harmonic_perfect_consonance_pct', 'metadata_root_key']`
- returned: `['texture_avg_wide_gaps_per_burst', 'tonality_prevalent_pitch_pct', 'tonality_out_of_key_notes']`

### 14. [pitched/combo]
**query:** vertical harmonic intervals: compound 14-semitone intervals stand out, the harmony is built mostly on major thirteenth intervals
- expected: `['profile_harmonic_intervals_pct_14_semitones', 'profile_harmonic_intervals_pct_21_semitones']`
- returned: `['profile_harmonic_intervals_pct_21_semitones']`

### 15. [pitched/combo]
**query:** the melody jumps by very wide intervals, 3-semitone stacks characterize the sound, the melody tends to drop down by major third
- expected: `['melodic_intervals_max_leap_semitones', 'profile_harmonic_intervals_pct_03_semitones', 'profile_melodic_intervals_pct_desc_4_semitones']`
- returned: `['melodic_intervals_absolute_median_semitones', 'profile_harmonic_intervals_pct_03_semitones', 'profile_melodic_intervals_pct_desc_4_semitones']`

### 16. [pitched/combo]
**query:** the harmony is built mostly on major thirteenth intervals, the line mostly rises in major sixth steps, the melody never moves down by major third
- expected: `['profile_harmonic_intervals_pct_21_semitones', 'profile_melodic_intervals_pct_asc_9_semitones', 'profile_melodic_intervals_pct_desc_4_semitones']`
- returned: `['profile_harmonic_intervals_pct_21_semitones', 'profile_melodic_intervals_pct_asc_9_semitones', 'melodic_intervals_pct_ascending', 'profile_melodic_intervals_pct_desc_3_semitones']`

### 17. [pitched/combo]
**query:** the overall sound is atonal and unstable, the melody rarely moves downward, the harmony is built mostly on major sixth intervals, the melody tends to drop down by octave
- expected: `['harmonic_dissonance_pct', 'melodic_intervals_pct_descending', 'profile_harmonic_intervals_pct_09_semitones', 'profile_melodic_intervals_pct_desc_12_semitones']`
- returned: `['tonality_out_of_key_notes', 'tonality_prevalent_pitch_pct', 'melodic_intervals_pct_descending', 'profile_harmonic_intervals_pct_09_semitones', 'profile_melodic_intervals_pct_desc_12_semitones']`

### 18. [pitched/combo]
**query:** no eighth-note length sustains, tritone clashes are prominent, the range is very tight and focused, the notes are spread far apart, single-note material is the norm
- expected: `['duration_8th_share', 'profile_harmonic_intervals_pct_06_semitones', 'register_spread_semitones', 'texture_avg_wide_gaps_per_burst', 'texture_pct_1_notes']`
- returned: `['duration_8th_share', 'profile_harmonic_intervals_pct_06_semitones', 'harmonic_dissonance_pct', 'register_spread_semitones', 'spacing_long_profile', 'texture_pct_1_notes']`

### 19. [pitched/combo]
**query:** the melody tends to jump up by major seventh, the melody tends to drop down by octave, the chords are voiced with wide spacing, the material is mostly chordal, extra chromatic notes creep in
- expected: `['profile_melodic_intervals_pct_asc_11_semitones', 'profile_melodic_intervals_pct_desc_12_semitones', 'texture_avg_wide_gaps_per_burst', 'texture_polyphonic_pct', 'tonality_unique_pitches_count_trend']`
- returned: `['profile_melodic_intervals_pct_asc_11_semitones', 'profile_melodic_intervals_pct_desc_12_semitones', 'texture_avg_wide_gaps_per_burst', 'texture_polyphonic_pct', 'tonality_out_of_key_notes']`

### 20. [pitched/combo]
**query:** the melody tends to jump up by minor third, the line mostly rises in perfect fifth steps, the ceiling pitch sits in the upper register, six or more notes ring together, the material is mostly monophonic
- expected: `['profile_melodic_intervals_pct_asc_3_semitones', 'profile_melodic_intervals_pct_asc_7_semitones', 'register_highest_note_midi', 'texture_pct_6plus_notes', 'texture_polyphonic_pct']`
- returned: `['profile_melodic_intervals_pct_asc_7_semitones', 'profile_melodic_intervals_pct_asc_3_semitones', 'register_highest_note_midi', 'texture_pct_6plus_notes', 'texture_pct_1_notes']`

### 21. [pitched/combo]
**query:** the harmony is rich and warm, the tonic pitch and mode are stated, the harmony contains no minor third intervals, very large jumps past the octave, the chordal stabs are held for a long time
- expected: `['harmonic_imperfect_consonance_pct', 'metadata_root_key', 'profile_harmonic_intervals_pct_03_semitones', 'profile_melodic_intervals_pct_asc_13plus_semitones', 'texture_polyphonic_burst_mean_duration_beats']`
- returned: `['harmonic_imperfect_consonance_pct', 'tonality_prevalent_pitch_pct', 'profile_harmonic_intervals_pct_03_semitones', 'melodic_intervals_max_leap_semitones', 'texture_polyphonic_burst_mean_duration_beats']`

### 22. [pitched/combo]
**query:** synth lead, the tonic pitch and mode are stated, the harmony contains no unison intervals, the harmony is built mostly on minor ninth intervals, a single line sitting below the chords
- expected: `['metadata_instrument_family', 'metadata_root_key', 'profile_harmonic_intervals_pct_00_semitones', 'profile_harmonic_intervals_pct_13_semitones', 'texture_monophonic_median_pitch']`
- returned: `['metadata_instrument_family', 'profile_harmonic_intervals_pct_13_semitones', 'profile_harmonic_intervals_pct_00_semitones', 'texture_monophonic_median_pitch', 'texture_polyphonic_pct', 'tonality_prevalent_pitch_pct', 'tonality_out_of_key_notes']`

## Direction flips (opposite pole — real errors, not mid)
### 1. [drums/combo] `drum_snare_clap_rhythmic_density_burstiness`
**query:** kick: beats two and four are rarely played but tight when played, kick: transition at the loop boundary, snare/clap: 32nd-note micro-timing varies, snare/clap: mostly even with one dense spike
- expected: `low` | got level: `Volatile Density` (high)

### 2. [pitched/combo] `profile_melodic_intervals_pct_desc_12_semitones`
**query:** the overall sound is atonal and unstable, the melody rarely moves downward, the harmony is built mostly on major sixth intervals, the melody tends to drop down by octave
- expected: `high` | got level: `Occasional` (low)

### 3. [pitched/combo] `profile_melodic_intervals_pct_asc_11_semitones`
**query:** the execution comes across loose and messy, the melody rarely moves upward, the melody tends to jump up by major seventh, extra chromatic notes creep in
- expected: `high` | got level: `Occasional` (low)

### 4. [pitched/combo] `texture_pct_6plus_notes`
**query:** the melody tends to jump up by minor third, the line mostly rises in perfect fifth steps, the ceiling pitch sits in the upper register, six or more notes ring together, the material is mostly monophonic
- expected: `high` | got level: `Occasional 6+ Notes` (low)
