import tempfile
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.cli import main
from midi_analyzer_tagger.storage import AnalysisDatabase


def _write_midi(path: Path, note_count: int = 1):
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    for i in range(note_count):
        inst.notes.append(
            pretty_midi.Note(pitch=60, velocity=100, start=i * 0.1, end=i * 0.1 + 0.05)
        )
    midi.instruments.append(inst)
    midi.write(str(path))


def test_analyze_command_writes_to_db_and_taxonomy():
    with tempfile.TemporaryDirectory() as tmpdir:
        midi_path = Path(tmpdir) / "file.mid"
        _write_midi(midi_path, note_count=5)

        db_path = Path(tmpdir) / "analysis.db"
        taxonomy_path = Path(tmpdir) / "taxonomy.json"

        assert main([
            "analyze",
            str(midi_path),
            "--db", str(db_path),
            "--taxonomy-json", str(taxonomy_path),
        ]) == 0

        assert db_path.exists()
        assert taxonomy_path.exists()

        with AnalysisDatabase(db_path) as db:
            rows = db.connection.execute(
                "SELECT path, family FROM files"
            ).fetchall()
            assert len(rows) == 1
            assert rows[0]["path"] == str(midi_path)
            assert rows[0]["family"] == "pitched"

            tags = db.connection.execute(
                "SELECT concept_name FROM tags"
            ).fetchall()
            concept_names = {row["concept_name"] for row in tags}
            assert "metadata_midi_program_number" in concept_names
            assert "rhythmic_density_average_events_per_beat" in concept_names


def test_analyze_folder_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_folder = Path(tmpdir) / "loops"
        input_folder.mkdir()
        _write_midi(input_folder / "file1.mid", note_count=5)
        _write_midi(input_folder / "sub" / "file2.mid", note_count=1)

        output_folder = Path(tmpdir) / "output"

        assert main(["analyze-folder", str(input_folder), "--output", str(output_folder)]) == 0

        db_path = output_folder / "analysis.db"
        taxonomy_path = output_folder / "taxonomy.json"
        assert db_path.exists()
        assert taxonomy_path.exists()

        with AnalysisDatabase(db_path) as db:
            rows = db.connection.execute(
                "SELECT path, family FROM files ORDER BY path"
            ).fetchall()
            paths = [row["path"] for row in rows]
            assert "file1.mid" in paths
            assert "sub/file2.mid" in paths
            assert all(row["family"] == "pitched" for row in rows)
