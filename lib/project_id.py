from __future__ import annotations

import hashlib
import os
import posixpath
import re
from pathlib import Path


_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:([/\\\\]|$)")
_MNT_DRIVE_RE = re.compile(r"^/mnt/([A-Za-z])/(.*)$")
_MSYS_DRIVE_RE = re.compile(r"^/([A-Za-z])/(.*)$")


def normalize_work_dir(value: str | Path) -> str:
    """
    Normalize a work_dir into a stable string for hashing and matching.

    Goals:
    - Be stable within a single environment (Linux/WSL/Windows/MSYS).
    - Reduce trivial path-format mismatches (slashes, drive letter casing, /mnt/<drive> mapping).
    - Avoid resolve() by default to reduce symlink/interop surprises.
    """
    raw = str(value).strip()
    if not raw:
        return ""

    # Expand "~" early.
    if raw.startswith("~"):
        try:
            raw = os.path.expanduser(raw)
        except Exception:
            pass

    # Absolutize when relative (best-effort).
    try:
        preview = raw.replace("\\", "/")
        is_abs = (
            preview.startswith("/")
            or preview.startswith("//")
            or preview.startswith("\\\\")
            or bool(_WIN_DRIVE_RE.match(preview))
        )
        if not is_abs:
            raw = str((Path.cwd() / Path(raw)).absolute())
    except Exception:
        pass

    s = raw.replace("\\", "/")

    # Map WSL mount paths to a Windows-like drive form for stable matching.
    m = _MNT_DRIVE_RE.match(s)
    if m:
        drive = m.group(1).lower()
        rest = m.group(2)
        s = f"{drive}:/{rest}"
    else:
        # Map MSYS /c/... to c:/...
        m = _MSYS_DRIVE_RE.match(s)
        if m and ("MSYSTEM" in os.environ or os.name == "nt"):
            drive = m.group(1).lower()
            rest = m.group(2)
            s = f"{drive}:/{rest}"

    # Collapse redundant separators and dot segments using POSIX semantics (we forced "/").
    if s.startswith("//"):
        prefix = "//"
        rest = posixpath.normpath(s[2:])
        s = prefix + rest.lstrip("/")
    else:
        s = posixpath.normpath(s)

    # Normalize Windows drive letter casing.
    if _WIN_DRIVE_RE.match(s):
        s = s[0].lower() + s[1:]

    return s


def _find_git_root(start_dir: Path) -> Path | None:
    """
    Find the root of the git repository by traversing up.
    Returns None if not in a git repository.
    """
    try:
        current = Path(start_dir).expanduser().absolute()
    except Exception:
        current = Path.cwd()

    # Traverse up to find .git directory
    while True:
        try:
            if (current / ".git").exists():
                return current
        except Exception:
            pass

        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent

    return None


def _find_ccb_config_root(start_dir: Path) -> Path | None:
    """
    Find a `.ccb/` (or legacy `.ccb_config/`) directory by traversing up.

    Search strategy:
    1. If in a git repository, search up to git root (prevents cross-project confusion)
    2. Otherwise, search up to 10 levels (prevents excessive traversal)

    This allows running `ask` from any subdirectory while preventing cross-project errors.
    """
    try:
        current = Path(start_dir).expanduser().absolute()
    except Exception:
        current = Path.cwd()

    # Find git repository boundary (if any)
    git_root = _find_git_root(current)

    # Traverse up to find .ccb directory
    max_levels = 10  # Limit traversal for non-git directories
    level = 0

    while True:
        try:
            cfg = current / ".ccb"
            if cfg.is_dir():
                return current
            legacy = current / ".ccb_config"
            if legacy.is_dir():
                return current
        except Exception:
            pass

        # Stop at git root boundary (if in git repo)
        if git_root and current == git_root:
            break

        # Stop at filesystem root
        parent = current.parent
        if parent == current:
            break

        # Stop after max levels (for non-git directories)
        if not git_root:
            level += 1
            if level >= max_levels:
                break

        current = parent

    return None


def compute_ccb_project_id(work_dir: Path) -> str:
    """
    Compute CCB's routing project id (ccb_project_id).

    Priority:
    - Current directory containing `.ccb/` (project anchor).
    - Current work_dir (fallback).
    """
    try:
        wd = Path(work_dir).expanduser().absolute()
    except Exception:
        wd = Path.cwd()

    # Priority 1: Current directory `.ccb/` only
    base = _find_ccb_config_root(wd)

    if base is None:
        base = wd

    norm = normalize_work_dir(base)
    if not norm:
        norm = normalize_work_dir(wd)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()
