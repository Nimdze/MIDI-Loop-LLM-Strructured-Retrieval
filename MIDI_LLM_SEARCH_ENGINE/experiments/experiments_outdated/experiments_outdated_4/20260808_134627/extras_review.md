# Test 2 — Extras review, grouped (20260808_134627)

35 genuine extras (2 test-issue cases excluded — see bottom) across 32 trials, grouped by pattern. Each shows full prompt + returned, extra marked **EXTRA**.

## Rhythmic density — burstiness ↔ bar-to-bar pair  (5)
- size1 drums | extra **drum_toms_others_rhythmic_density_bar_to_bar_evolution** = 'Constant Bar Event Density'
  Prompt: the toms steady even density
  Expected: drum_toms_others_rhythmic_density_burstiness
  Returned: drum_toms_others_rhythmic_density_burstiness (Uniform Density), drum_toms_others_rhythmic_density_bar_to_bar_evolution (Constant Bar Event Density)  **EXTRA**
- size7 drums | extra **drum_hats_cymbals_rhythmic_density_bar_to_bar_evolution** = 'Constant Bar Event Density'
  Prompt: the hats/cymbals steady even density, the kick the volume increases gradually through the track, the kick every offbeat lands in the pocket, the kick the offbeat upbeats are accented regularly, the kick notes are spaced a quarter note apart, the Pedal Hat is prominent, the snare/clap drum fill at the end of the phrase, the snare/clap the general onset spacing profile is short and compact
  Expected: drum_hats_cymbals_rhythmic_density_burstiness, drum_kick_dynamics_intensity_trend, drum_kick_grid_success_pct_offbeat, drum_kick_grid_attempt_pct_offbeat, drum_kick_spacing_quarter_share, drum_prevalence_hats_cymbals_pedal_hat, drum_snare_clap_rhythmic_density_turnaround_shift, drum_snare_clap_spacing_short_profile
  Returned: drum_hats_cymbals_rhythmic_density_bar_to_bar_evolution (Constant Bar Event Density)  **EXTRA**, drum_hats_cymbals_rhythmic_density_burstiness (Uniform Density), drum_kick_dynamics_intensity_trend (Building Intensity), drum_kick_grid_success_pct_offbeat (High Success), drum_kick_grid_attempt_pct_offbeat (High Attempts), drum_kick_spacing_quarter_share (Defining Quarter Note Spacing), drum_prevalence_hats_cymbals_pedal_hat (Primary Pedal Hat), drum_snare_clap_rhythmic_density_turnaround_shift (Turnaround Fill), drum_snare_clap_spacing_short_profile (Defining Short Spacing)
- size9 drums | extra **drum_toms_others_rhythmic_density_bar_to_bar_evolution** = 'Constant Bar Event Density'
  Prompt: the hats/cymbals the volume increases gradually through the track, the hats/cymbals attacks every half note creating an open feel, the kick the whole performance is very loud and aggressive, the Kick 2 is prominent, the Clap is prominent, the snare/clap gaps longer than a whole measure, the toms humanized natural feel, the toms steady even density, the toms drum fill at the end of the phrase
  Expected: drum_hats_cymbals_dynamics_intensity_trend, drum_hats_cymbals_spacing_half_share, drum_kick_dynamics_average_velocity, drum_prevalence_kick_kick_2, drum_prevalence_snare_clap_clap, drum_snare_clap_spacing_above_whole_share, drum_toms_others_groove_micro_jitter, drum_toms_others_rhythmic_density_burstiness, drum_toms_others_rhythmic_density_turnaround_shift
  Returned: drum_hats_cymbals_dynamics_intensity_trend (Building Intensity), drum_hats_cymbals_spacing_half_share (Defining Half Note Spacing), drum_kick_dynamics_average_velocity (Hard/Aggressive Velocity), drum_prevalence_kick_kick_2 (Primary Kick 2), drum_prevalence_snare_clap_clap (Primary Clap), drum_snare_clap_spacing_above_whole_share (Present Above Whole Note Spacing), drum_toms_others_groove_micro_jitter (Organic Micro Execution), drum_toms_others_rhythmic_density_burstiness (Uniform Density), drum_toms_others_rhythmic_density_bar_to_bar_evolution (Constant Bar Event Density)  **EXTRA**, drum_toms_others_rhythmic_density_turnaround_shift (Turnaround Fill)
- size2 drums | extra **drum_snare_clap_rhythmic_density_bar_to_bar_evolution** = 'Constant Bar Event Density'
  Prompt: the hats/cymbals the two and four positions land with perfect accuracy, the hats/cymbals the two and four positions are attacked very consistently, the snare/clap steady even density
  Expected: drum_hats_cymbals_grid_success_pct_2and4, drum_hats_cymbals_grid_attempt_pct_2and4, drum_snare_clap_rhythmic_density_burstiness
  Returned: drum_hats_cymbals_grid_success_pct_2and4 (High Success), drum_hats_cymbals_grid_attempt_pct_2and4 (High Attempts), drum_snare_clap_rhythmic_density_burstiness (Uniform Density), drum_snare_clap_rhythmic_density_bar_to_bar_evolution (Constant Bar Event Density)  **EXTRA**
- size6 pitched | extra **rhythmic_density_bar_to_bar_evolution** = 'Constant Bar Event Density'
  Prompt: the longest note is very extended, the rhythm has a pronounced swing feel, vertical intervals are mostly minor sixth, melody mostly leaps up by major sixth, dropping to deep bass notes, steady even density
  Expected: duration_max_length_beats, groove_swing_shuffle_ratio, profile_harmonic_intervals_pct_08_semitones, profile_melodic_intervals_pct_asc_9_semitones, register_lowest_note_midi, rhythmic_density_burstiness
  Returned: duration_max_length_beats (Contains Long Sustained Notes (3-4 Bars)), groove_swing_shuffle_ratio (Heavy Swing / Shuffle), profile_harmonic_intervals_pct_08_semitones (Primary), profile_melodic_intervals_pct_asc_9_semitones (Primary), register_lowest_note_midi (Register: Bass), rhythmic_density_burstiness (Uniform Density), rhythmic_density_bar_to_bar_evolution (Constant Bar Event Density)  **EXTRA**

## Other (dynamics / spacing / texture)  (6)
- size1 drums | extra **drum_hats_cymbals_rhythmic_density_burstiness** = 'Steady Density'
  Prompt: the hats/cymbals steady 16th note spacing between attacks
  Expected: drum_hats_cymbals_spacing_16th_share
  Returned: drum_hats_cymbals_spacing_16th_share (Defining 16th Note Spacing), drum_hats_cymbals_rhythmic_density_burstiness (Steady Density)  **EXTRA**
- size1 drums | extra **drum_snare_clap_rhythmic_density_burstiness** = 'Volatile Density'
  Prompt: the snare/clap drum fill at the end of the phrase
  Expected: drum_snare_clap_rhythmic_density_turnaround_shift
  Returned: drum_snare_clap_rhythmic_density_turnaround_shift (Turnaround Fill), drum_snare_clap_rhythmic_density_burstiness (Volatile Density)  **EXTRA**
- size3 drums | extra **drum_snare_clap_dynamics_accents_presence** = 'Contains Dynamic Accents'
  Prompt: the hats/cymbals gaps longer than a whole measure, the kick attacks every half note creating an open feel, the snare/clap each beat three lands on the grid, the snare/clap beat three receives a strong attack
  Expected: drum_hats_cymbals_spacing_above_whole_share, drum_kick_spacing_half_share, drum_snare_clap_grid_success_pct_beat3, drum_snare_clap_grid_attempt_pct_beat3
  Returned: drum_hats_cymbals_spacing_above_whole_share (Significant Above Whole Note Spacing), drum_kick_spacing_half_share (Defining Half Note Spacing), drum_snare_clap_grid_attempt_pct_beat3 (High Attempts), drum_snare_clap_grid_success_pct_beat3 (High Success), drum_snare_clap_dynamics_accents_presence (Contains Dynamic Accents)  **EXTRA**
- size5 pitched | extra **spacing_32nd_share** = 'Occasional 32nd Note Spacing'
  Prompt: notes are very short 32nd note bursts, most notes are sustained a long time, sits in the mid register, very busy frantic rhythm, chords with six plus notes
  Expected: duration_32nd_share, duration_long_profile, register_median_note_midi, rhythmic_density_average_events_per_beat, texture_pct_6plus_notes
  Returned: duration_long_profile (Primary Long Duration), duration_32nd_share (Occasional 32nd Note Duration), spacing_32nd_share (Occasional 32nd Note Spacing)  **EXTRA**, register_median_note_midi (Register: Mid), rhythmic_density_average_events_per_beat (Frantic), texture_pct_6plus_notes (Significant 6+ Notes)
- size5 pitched | extra **texture_polyphonic_pct** = 'Significant Chordal (3+ Notes)'
  Prompt: vertical intervals are mostly octave, huge downward leaps beyond an octave, melody mostly falls down by minor third, sits in the mid register, a bass line under the chords
  Expected: profile_harmonic_intervals_pct_12_semitones, profile_melodic_intervals_pct_desc_13plus_semitones, profile_melodic_intervals_pct_desc_3_semitones, register_median_note_midi, texture_monophonic_median_pitch
  Returned: profile_harmonic_intervals_pct_12_semitones (Primary), profile_melodic_intervals_pct_desc_13plus_semitones (Present), profile_melodic_intervals_pct_desc_3_semitones (Primary), register_median_note_midi (Register: Mid), texture_monophonic_median_pitch (Register: Bass), texture_polyphonic_pct (Significant Chordal (3+ Notes))  **EXTRA**
- size2 pitched | extra **dynamics_accents_presence** = 'Contains Dynamic Accents'
  Prompt: every offbeat lands in the pocket, the offbeat upbeats are accented regularly, melody mostly leaps up by octave
  Expected: grid_success_pct_offbeat, grid_attempt_pct_offbeat, profile_melodic_intervals_pct_asc_12_semitones
  Returned: grid_success_pct_offbeat (High Success), grid_attempt_pct_offbeat (High Attempts), dynamics_accents_presence (Contains Dynamic Accents)  **EXTRA**, profile_melodic_intervals_pct_asc_12_semitones (Primary), melodic_intervals_pct_ascending (Defining Ascending Motion)

## Melodic direction — descending (specific + aggregate)  (8)
- size1 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: melody mostly falls down by tritone
  Expected: profile_melodic_intervals_pct_desc_6_semitones
  Returned: profile_melodic_intervals_pct_desc_6_semitones (Primary), melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**
- size2 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: melody mostly falls down by minor seventh, melody mostly falls down by perfect fourth
  Expected: profile_melodic_intervals_pct_desc_10_semitones, profile_melodic_intervals_pct_desc_5_semitones
  Returned: melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**, profile_melodic_intervals_pct_desc_10_semitones (Significant), profile_melodic_intervals_pct_desc_5_semitones (Significant)
- size3 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: melody mostly falls down by octave, a long break with nothing ringing, chords tend to have three notes
  Expected: profile_melodic_intervals_pct_desc_12_semitones, spacing_max_silence_beats, texture_pct_3_notes
  Returned: melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**, profile_melodic_intervals_pct_desc_12_semitones (Primary), spacing_max_silence_beats (Long Max Silence (1-2 Bars)), texture_pct_3_notes (Primary 3 Notes)
- size4 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: melody mostly falls down by major seventh, the general onset spacing profile is long and spread out, the general onset spacing profile is short and compact, pitch vocabulary expands over time
  Expected: profile_melodic_intervals_pct_desc_11_semitones, spacing_long_profile, spacing_short_profile, tonality_unique_pitches_count_trend
  Returned: melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**, profile_melodic_intervals_pct_desc_11_semitones (Primary), spacing_long_profile (Primary Long Spacing), spacing_short_profile (Primary Short Spacing), tonality_unique_pitches_count_trend (Expanding Pitch Vocabulary)
- size5 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: notes are held for a half note, the volume increases gradually through the track, vertical intervals are mostly minor tenth, melody mostly falls down by tritone, most chords have four notes
  Expected: duration_half_share, dynamics_intensity_trend, profile_harmonic_intervals_pct_15_semitones, profile_melodic_intervals_pct_desc_6_semitones, texture_pct_4_notes
  Returned: duration_half_share (Primary Half Note Duration), dynamics_intensity_trend (Building Intensity), profile_harmonic_intervals_pct_15_semitones (Primary), melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**, profile_melodic_intervals_pct_desc_6_semitones (Primary), texture_pct_4_notes (Primary 4 Notes)
- size6 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: the even bar downbeat is attacked regularly, the even bar downbeats are accurate, melody mostly falls down by major third, melody mostly falls down by perfect fourth, register shifts dramatically, the general onset spacing profile is long and spread out, pitch vocabulary expands over time
  Expected: grid_attempt_pct_even1, grid_success_pct_even1, profile_melodic_intervals_pct_desc_4_semitones, profile_melodic_intervals_pct_desc_5_semitones, register_boundary_shift_semitones, spacing_long_profile, tonality_unique_pitches_count_trend
  Returned: grid_attempt_pct_even1 (High Attempts), grid_success_pct_even1 (High Success), melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**, profile_melodic_intervals_pct_desc_4_semitones (Significant), profile_melodic_intervals_pct_desc_5_semitones (Significant), register_boundary_shift_semitones (Active Register Migration), spacing_long_profile (Primary Long Spacing), tonality_unique_pitches_count_trend (Expanding Pitch Vocabulary)
- size7 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: note lengths are moderate, vertical intervals are mostly minor thirteenth, melody mostly falls down by minor third, sits in the mid register, wide open chord voicings, texture is mostly dyads two notes, strong tonal center anchored
  Expected: duration_medium_profile, profile_harmonic_intervals_pct_20_semitones, profile_melodic_intervals_pct_desc_3_semitones, register_median_note_midi, texture_avg_wide_gaps_per_burst, texture_pct_2_notes, tonality_prevalent_pitch_pct
  Returned: duration_medium_profile (Primary Medium Duration), profile_harmonic_intervals_pct_20_semitones (Primary), melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**, profile_melodic_intervals_pct_desc_3_semitones (Primary), register_median_note_midi (Register: Mid), texture_avg_wide_gaps_per_burst (Big Chordal Spread), texture_pct_2_notes (Primary 2 Notes), tonality_prevalent_pitch_pct (Anchor Centered)
- size2 pitched | extra **melodic_intervals_pct_descending** = 'Primary Descending Motion'
  Prompt: very dissonant tense harmony, melody mostly falls down by major second
  Expected: harmonic_dissonance_pct, profile_melodic_intervals_pct_desc_2_semitones
  Returned: harmonic_dissonance_pct (Primary Dissonance), melodic_intervals_pct_descending (Primary Descending Motion)  **EXTRA**, profile_melodic_intervals_pct_desc_2_semitones (Primary)

## Melodic direction — ascending (specific + aggregate)  (6)
- size1 pitched | extra **melodic_intervals_pct_ascending** = 'Primary Ascending Motion'
  Prompt: melody mostly leaps up by minor sixth
  Expected: profile_melodic_intervals_pct_asc_8_semitones
  Returned: profile_melodic_intervals_pct_asc_8_semitones (Primary), melodic_intervals_pct_ascending (Primary Ascending Motion)  **EXTRA**, melodic_intervals_absolute_median_semitones (Angular / Leaping Melodic Motion)
- size1 pitched | extra **melodic_intervals_pct_ascending** = 'Primary Ascending Motion'
  Prompt: melody mostly leaps up by minor second
  Expected: profile_melodic_intervals_pct_asc_1_semitones
  Returned: melodic_intervals_pct_ascending (Primary Ascending Motion)  **EXTRA**, profile_melodic_intervals_pct_asc_1_semitones (Primary)
- size2 pitched | extra **melodic_intervals_pct_ascending** = 'Primary Ascending Motion'
  Prompt: focused narrow interval palette, melody mostly leaps up by tritone
  Expected: melodic_interval_vocabulary_count, profile_melodic_intervals_pct_asc_6_semitones
  Returned: melodic_interval_vocabulary_count (Focused Melodic Interval Palette), melodic_intervals_pct_ascending (Primary Ascending Motion)  **EXTRA**, profile_melodic_intervals_pct_asc_6_semitones (Primary), melodic_intervals_absolute_median_semitones (Angular / Leaping Melodic Motion)
- size2 pitched | extra **melodic_intervals_pct_ascending** = 'Primary Ascending Motion'
  Prompt: melody mostly leaps up by major sixth, pitch vocabulary expands over time
  Expected: profile_melodic_intervals_pct_asc_9_semitones, tonality_unique_pitches_count_trend
  Returned: profile_melodic_intervals_pct_asc_9_semitones (Primary), melodic_intervals_pct_ascending (Primary Ascending Motion)  **EXTRA**, tonality_unique_pitches_count_trend (Expanding Pitch Vocabulary)
- size3 pitched | extra **melodic_intervals_pct_ascending** = 'Primary Ascending Motion'
  Prompt: vertical intervals are mostly major seventh, melody mostly leaps up by minor third, melody mostly leaps up by perfect fifth
  Expected: profile_harmonic_intervals_pct_11_semitones, profile_melodic_intervals_pct_asc_3_semitones, profile_melodic_intervals_pct_asc_7_semitones
  Returned: profile_harmonic_intervals_pct_11_semitones (Primary), melodic_intervals_pct_ascending (Primary Ascending Motion)  **EXTRA**, profile_melodic_intervals_pct_asc_3_semitones (Significant), profile_melodic_intervals_pct_asc_7_semitones (Significant)
- size2 pitched | extra **melodic_intervals_pct_ascending** = 'Defining Ascending Motion'
  Prompt: every offbeat lands in the pocket, the offbeat upbeats are accented regularly, melody mostly leaps up by octave
  Expected: grid_success_pct_offbeat, grid_attempt_pct_offbeat, profile_melodic_intervals_pct_asc_12_semitones
  Returned: grid_success_pct_offbeat (High Success), grid_attempt_pct_offbeat (High Attempts), dynamics_accents_presence (Contains Dynamic Accents), profile_melodic_intervals_pct_asc_12_semitones (Primary), melodic_intervals_pct_ascending (Defining Ascending Motion)  **EXTRA**

## Melodic span / leap  (3)
- size1 pitched | extra **melodic_intervals_absolute_median_semitones** = 'Angular / Leaping Melodic Motion'
  Prompt: melody mostly leaps up by minor sixth
  Expected: profile_melodic_intervals_pct_asc_8_semitones
  Returned: profile_melodic_intervals_pct_asc_8_semitones (Primary), melodic_intervals_pct_ascending (Primary Ascending Motion), melodic_intervals_absolute_median_semitones (Angular / Leaping Melodic Motion)  **EXTRA**
- size2 pitched | extra **melodic_intervals_absolute_median_semitones** = 'Angular / Leaping Melodic Motion'
  Prompt: focused narrow interval palette, melody mostly leaps up by tritone
  Expected: melodic_interval_vocabulary_count, profile_melodic_intervals_pct_asc_6_semitones
  Returned: melodic_interval_vocabulary_count (Focused Melodic Interval Palette), melodic_intervals_pct_ascending (Primary Ascending Motion), profile_melodic_intervals_pct_asc_6_semitones (Primary), melodic_intervals_absolute_median_semitones (Angular / Leaping Melodic Motion)  **EXTRA**
- size4 pitched | extra **melodic_intervals_max_leap_semitones** = 'Contains Extreme Leaps (>= Octave)'
  Prompt: vertical intervals are mostly major thirteenth, vertical intervals are mostly double octave / fifteenth, huge upward leaps beyond an octave, busy rhythmic chord comping
  Expected: profile_harmonic_intervals_pct_21_semitones, profile_harmonic_intervals_pct_24_semitones, profile_melodic_intervals_pct_asc_13plus_semitones, texture_polyphonic_burst_rate
  Returned: profile_harmonic_intervals_pct_21_semitones (Primary), profile_harmonic_intervals_pct_24_semitones (Primary), profile_melodic_intervals_pct_asc_13plus_semitones (Primary), melodic_intervals_max_leap_semitones (Contains Extreme Leaps (>= Octave))  **EXTRA**, texture_polyphonic_burst_rate (Dense Chordal Hits)

## Harmonic consonance — dissonance (specific + aggregate)  (2)
- size2 pitched | extra **harmonic_dissonance_pct** = 'Primary Dissonance'
  Prompt: vertical intervals are mostly tritone / augmented fourth / diminished fifth, very narrow focused range
  Expected: profile_harmonic_intervals_pct_06_semitones, register_spread_semitones
  Returned: profile_harmonic_intervals_pct_06_semitones (Primary), harmonic_dissonance_pct (Primary Dissonance)  **EXTRA**, register_spread_semitones (Compact Pitch Range (< 1 Octave))
- size2 pitched | extra **harmonic_dissonance_pct** = 'Primary Dissonance'
  Prompt: there are strong accent hits that stand out, vertical intervals are mostly major fourteenth
  Expected: dynamics_accents_presence, profile_harmonic_intervals_pct_23_semitones
  Returned: dynamics_accents_presence (Contains Dynamic Accents), profile_harmonic_intervals_pct_23_semitones (Primary), harmonic_dissonance_pct (Primary Dissonance)  **EXTRA**

## Harmonic consonance — perfect consonance (specific + aggregate)  (1)
- size2 pitched | extra **harmonic_perfect_consonance_pct** = 'Primary Perfect Consonance'
  Prompt: lots of stepwise scalar motion, vertical intervals are mostly perfect fifth
  Expected: melodic_intervals_absolute_median_semitones, profile_harmonic_intervals_pct_07_semitones
  Returned: melodic_intervals_absolute_median_semitones (Stepwise / Scalar Melodic Motion), profile_harmonic_intervals_pct_07_semitones (Primary), harmonic_perfect_consonance_pct (Primary Perfect Consonance)  **EXTRA**

## Off-by-one semitone (BAD)  (3)
- size3 pitched | extra **profile_harmonic_intervals_pct_21_semitones** = 'Primary'
  Prompt: notes are very short 32nd note bursts, synth lead, vertical intervals are mostly minor thirteenth
  Expected: duration_32nd_share, metadata_instrument_family, profile_harmonic_intervals_pct_20_semitones
  Returned: duration_32nd_share (Primary 32nd Note Duration), metadata_instrument_family (Synth Lead), profile_harmonic_intervals_pct_21_semitones (Primary)  **EXTRA**
- size4 pitched | extra **profile_harmonic_intervals_pct_20_semitones** = 'Primary'
  Prompt: the offbeat upbeats are accented regularly, every offbeat lands in the pocket, vertical intervals are mostly twelfth / perfect twelfth, huge upward leaps beyond an octave, notes are spaced a quarter note apart
  Expected: grid_attempt_pct_offbeat, grid_success_pct_offbeat, profile_harmonic_intervals_pct_19_semitones, profile_melodic_intervals_pct_asc_13plus_semitones, spacing_quarter_share
  Returned: grid_attempt_pct_offbeat (High Attempts), grid_success_pct_offbeat (High Success), profile_harmonic_intervals_pct_20_semitones (Primary)  **EXTRA**, profile_melodic_intervals_pct_asc_13plus_semitones (Present), spacing_quarter_share (Defining Quarter Note Spacing)
- size8 pitched | extra **profile_melodic_intervals_pct_desc_3_semitones** = 'Primary'
  Prompt: the volume increases gradually through the track, vertical intervals are mostly perfect fourth, vertical intervals are mostly minor fourteenth, melody mostly leaps up by major second, melody mostly falls down by major third, notes are spaced a quarter note apart, most chords have four notes, chords with six plus notes
  Expected: dynamics_intensity_trend, profile_harmonic_intervals_pct_05_semitones, profile_harmonic_intervals_pct_22_semitones, profile_melodic_intervals_pct_asc_2_semitones, profile_melodic_intervals_pct_desc_4_semitones, spacing_quarter_share, texture_pct_4_notes, texture_pct_6plus_notes
  Returned: dynamics_intensity_trend (Building Intensity), profile_harmonic_intervals_pct_05_semitones (Primary), profile_harmonic_intervals_pct_22_semitones (Primary), profile_melodic_intervals_pct_asc_2_semitones (Primary), profile_melodic_intervals_pct_desc_3_semitones (Primary)  **EXTRA**, spacing_quarter_share (Primary Quarter Note Spacing), texture_pct_4_notes (Primary 4 Notes), texture_pct_6plus_notes (Occasional 6+ Notes)

## Harmonic specific interval (octave borderline)  (1)
- size6 pitched | extra **profile_harmonic_intervals_pct_12_semitones** = 'Significant'
  Prompt: notes sustain a full whole note, the offbeat upbeats are accented regularly, every offbeat lands in the pocket, humanized natural feel, lots of open fifths and power chords, vertical intervals are mostly minor thirteenth, melody mostly leaps up by perfect fifth
  Expected: duration_whole_share, grid_attempt_pct_offbeat, grid_success_pct_offbeat, groove_micro_jitter, harmonic_perfect_consonance_pct, profile_harmonic_intervals_pct_20_semitones, profile_melodic_intervals_pct_asc_7_semitones
  Returned: duration_whole_share (Primary Whole Note Duration), grid_attempt_pct_offbeat (Moderate Attempts), grid_success_pct_offbeat (High Success), groove_micro_jitter (Organic Micro Execution), profile_harmonic_intervals_pct_07_semitones (Significant), profile_harmonic_intervals_pct_12_semitones (Significant)  **EXTRA**, profile_harmonic_intervals_pct_20_semitones (Primary), profile_melodic_intervals_pct_asc_7_semitones (Primary)

## Excluded — test issues (interval the prompt explicitly named, omitted by expected)
- size6 | extra **profile_harmonic_intervals_pct_07_semitones** = 'Significant'
  Prompt: notes sustain a full whole note, the offbeat upbeats are accented regularly, every offbeat lands in the pocket, humanized natural feel, lots of open fifths and power chords, vertical intervals are mostly minor thirteenth, melody mostly leaps up by perfect fifth
  Expected: duration_whole_share, grid_attempt_pct_offbeat, grid_success_pct_offbeat, groove_micro_jitter, harmonic_perfect_consonance_pct, profile_harmonic_intervals_pct_20_semitones, profile_melodic_intervals_pct_asc_7_semitones
  Returned: duration_whole_share (Primary Whole Note Duration), grid_attempt_pct_offbeat (Moderate Attempts), grid_success_pct_offbeat (High Success), groove_micro_jitter (Organic Micro Execution), profile_harmonic_intervals_pct_07_semitones (Significant)  **EXTRA**, profile_harmonic_intervals_pct_12_semitones (Significant), profile_harmonic_intervals_pct_20_semitones (Primary), profile_melodic_intervals_pct_asc_7_semitones (Primary)
- size9 | extra **profile_harmonic_intervals_pct_07_semitones** = 'Significant'
  Prompt: each beat three lands on the grid, beat three receives a strong attack, lots of open fifths and power chords, vertical intervals are mostly minor tenth, vertical intervals are mostly major thirteenth, melody mostly leaps up by tritone, sits in the mid register, attacks land on every eighth note, the general onset spacing profile is short and compact, wide open chord voicings
  Expected: grid_success_pct_beat3, grid_attempt_pct_beat3, harmonic_perfect_consonance_pct, profile_harmonic_intervals_pct_15_semitones, profile_harmonic_intervals_pct_21_semitones, profile_melodic_intervals_pct_asc_6_semitones, register_median_note_midi, spacing_8th_share, spacing_short_profile, texture_avg_wide_gaps_per_burst
  Returned: grid_success_pct_beat3 (High Success), grid_attempt_pct_beat3 (High Attempts), profile_harmonic_intervals_pct_07_semitones (Significant)  **EXTRA**, harmonic_perfect_consonance_pct (Significant Perfect Consonance), profile_harmonic_intervals_pct_15_semitones (Primary), profile_harmonic_intervals_pct_21_semitones (Primary), profile_melodic_intervals_pct_asc_6_semitones (Primary), register_median_note_midi (Register: Mid), spacing_8th_share (Defining 8th Note Spacing), spacing_short_profile (Primary Short Spacing), texture_avg_wide_gaps_per_burst (Big Chordal Spread)
