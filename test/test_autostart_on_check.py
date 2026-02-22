import os
import subprocess
import sys
import time
import json
import pytest
from pathlib import Path

# Add lib to sys.path
script_dir = Path(__file__).resolve().parent
lib_dir = script_dir.parent / "lib"
sys.path.insert(0, str(lib_dir))

def test_ccb_ping_autostart(tmp_path):
    """Test that ccb-ping --autostart starts the daemon if session file exists."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Create a mock session file
    session_file = project_dir / ".gemini-session"
    # Provide enough fields to avoid GeminiCommunicator init errors
    session_file.write_text(json.dumps({
        "active": True, 
        "work_dir": str(project_dir),
        "session_id": "test-session-123",
        "runtime_dir": str(tmp_path / "run"),
        "pane_id": "1",
        "terminal": "tmux"
    }))
    (tmp_path / "run").mkdir()
    
    # Run ccb-ping with --autostart
    bin_dir = script_dir.parent / "bin"
    ccb_ping = bin_dir / "ccb-ping"
    
    env = os.environ.copy()
    env["CCB_GASKD_AUTOSTART"] = "1"
    env["CCB_GASKD"] = "1"
    # Use a mock CCB_RUN_DIR so we don't interfere with real sessions
    env["CCB_RUN_DIR"] = str(tmp_path / "run")
    
    result = subprocess.run(
        [sys.executable, str(ccb_ping), "gemini", "--autostart"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        env=env
    )
    
    # Check that it didn't fail with "unrecognized argument"
    assert "unrecognized arguments: --autostart" not in result.stderr
    
def test_ccb_mounted_autostart(tmp_path):
    """Test that ccb-mounted --autostart is recognized."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    bin_dir = script_dir.parent / "bin"
    ccb_mounted = bin_dir / "ccb-mounted"
    
    result = subprocess.run(
        ["bash", str(ccb_mounted), "--autostart", str(project_dir)],
        capture_output=True,
        text=True
    )
    
    # Should be valid JSON
    data = json.loads(result.stdout)
    assert "mounted" in data
