from __future__ import annotations

import json
from pathlib import Path

from claude_comm import ClaudeLogReader
from askd.adapters.claude import _extract_reply_from_session


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")


def test_extract_reply_from_session(tmp_path) -> None:
    req_id = "20260201-000000-000-42"
    reader = ClaudeLogReader(root=tmp_path, work_dir=tmp_path)
    project_dir = reader._project_dir()
    project_dir.mkdir(parents=True, exist_ok=True)
    session_old = project_dir / "old.jsonl"
    session_new = project_dir / "new.jsonl"
    entries = [
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": f"CCB_BEGIN: {req_id}\\nHello"}],
            },
        },
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": f"World\\nCCB_DONE: {req_id}"}],
            },
        },
    ]
    _write_jsonl(session_new, entries)
    _write_jsonl(session_old, [])
    reader.set_preferred_session(session_old)
    reply, done_seen = _extract_reply_from_session(reader, req_id)
    assert done_seen is True
    assert "Hello" in reply
    assert "World" in reply
