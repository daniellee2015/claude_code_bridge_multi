Use `gpend` to fetch latest reply from Gemini logs.

WARNING: Only use when user EXPLICITLY requests. Do NOT use proactively after gask.

Trigger conditions (ALL must match):
- User EXPLICITLY mentions gpend/Gpend
- Or user asks to "view gemini reply" / "show gemini response"

Execution:
- `gpend` - fetch latest reply: `Bash(gpend)`
- `gpend N` - fetch last N Q&A pairs: `Bash(gpend N)`

Output: stdout = reply text, exit code 0 = success, 2 = no reply
