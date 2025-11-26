from pathlib import Path
import tempfile
from src.client.nsfw_tool import write_errors_csv


def test_write_errors_csv_creates_file_and_rows():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        results = [
            {"path": base / "a.png", "error": "HTTP 500"},
            {"path": base / "b.png", "error": None},
            {"path": base / "c.png", "error": "timeout"},
        ]
        out = write_errors_csv(base, results)
        assert out.exists()
        content = out.read_text().strip().splitlines()
        assert content[0] == "file,error"
        # two error rows expected
        assert len(content) == 3
