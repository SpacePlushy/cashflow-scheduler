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


def test_cli_verify_prints_statuses():
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    out = result.stdout
    # Core lines
    assert "DP Objective:" in out
    assert "CP-SAT Objective:" in out
    # New status section
    assert "Solver statuses:" in out
    assert "- workdays:" in out
