Use `cpend` to fetch latest reply from Codex logs.

WARNING: Only use when user EXPLICITLY requests. Do NOT use proactively after cask.

Trigger conditions (ALL must match):
- User EXPLICITLY mentions cpend/Cpend
- Or user asks to "view codex reply" / "show codex response"

Execution:
- `cpend` - fetch latest reply: `Bash(cpend)`
- `cpend N` - fetch last N Q&A pairs: `Bash(cpend N)`

Output: stdout = reply text, exit code 0 = success, 2 = no reply
