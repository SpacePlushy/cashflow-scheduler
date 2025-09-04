from typer.testing import CliRunner

from cashflow.cli import app


runner = CliRunner()


def test_cli_show_succeeds_and_prints_table():
    result = runner.invoke(app, ["show"])
    assert result.exit_code == 0
    out = result.stdout
    assert "| Day | Opening | Deposits | Action | Net | Bills | Closing |" in out
    assert "Final closing:" in out


def test_cli_export_writes_file(tmp_path):
    out_path = tmp_path / "schedule.md"
    result = runner.invoke(app, ["export", "--out", str(out_path)])
    assert result.exit_code == 0
    assert out_path.exists()
    text = out_path.read_text()
    assert "Objective:" in text
