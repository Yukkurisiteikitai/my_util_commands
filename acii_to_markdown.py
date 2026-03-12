#!/usr/bin/env python3
"""
ASCII box table → Markdown table converter
Handles multi-line cells by joining them with spaces.

Usage:
  python ascii_to_markdown.py               # convert built-in sample
  python ascii_to_markdown.py --clip        # read from clipboard, write result back to clipboard
  python ascii_to_markdown.py input.txt     # convert a file
"""

import subprocess
import sys


def parse_ascii_table(text: str) -> list[list[str]]:
    """Parse ASCII box table into a 2D list of cell strings."""
    lines = text.splitlines()

    # Keep only lines that are actual row lines (start with │)
    row_lines = [l for l in lines if l.startswith("  │") or l.startswith("│")]

    if not row_lines:
        return []

    # Group consecutive row lines into logical rows (separated by ├─ or └─ or ┌─ borders)
    # Strategy: collect lines between border rows
    all_lines = text.splitlines()

    groups: list[list[str]] = []
    current: list[str] = []

    for line in all_lines:
        stripped = line.strip()
        if stripped.startswith("│"):
            current.append(stripped)
        else:
            if current:
                groups.append(current)
                current = []

    if current:
        groups.append(current)

    # Each group is a logical row; parse columns from each line
    rows: list[list[str]] = []
    for group in groups:
        # Parse number of columns from first line
        num_cols = group[0].count("│") - 1
        if num_cols <= 0:
            continue

        # Accumulate cell text per column across the group's lines
        col_texts: list[list[str]] = [[] for _ in range(num_cols)]

        for line in group:
            # Split by │
            parts = line.split("│")
            # parts[0] is empty (before first │), parts[1..n] are cells, parts[n+1] may be empty
            cells = parts[1 : num_cols + 1]
            for i, cell in enumerate(cells):
                cell_stripped = cell.strip()
                if cell_stripped:
                    col_texts[i].append(cell_stripped)

        # Join multi-line cell content
        row = [" ".join(parts) if parts else "" for parts in col_texts]
        rows.append(row)

    return rows


def rows_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""

    num_cols = max(len(r) for r in rows)

    # Pad rows to same width
    rows = [r + [""] * (num_cols - len(r)) for r in rows]

    header = rows[0]
    body = rows[1:]

    # Column widths
    widths = [max(len(header[c]), *(len(r[c]) for r in body), 3) for c in range(num_cols)]

    def fmt_row(cells):
        return "| " + " | ".join(cells[c].ljust(widths[c]) for c in range(num_cols)) + " |"

    separator = "| " + " | ".join("-" * widths[c] for c in range(num_cols)) + " |"

    lines = [fmt_row(header), separator] + [fmt_row(r) for r in body]
    return "\n".join(lines)


def convert(text: str) -> str:
    rows = parse_ascii_table(text)
    return rows_to_markdown(rows)


# ── Demo ──────────────────────────────────────────────────────────────────────
SAMPLE = """
  ┌───────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                               Task                                │                                             Status                                              │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ SQL security (006_fix_classify_atomic.sql)                        │ auth.uid() replaces p_user_id, SET search_path = public added, counter only increments on       │
  │                                                                   │ actual insert                                                                                   │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Repo caller (SupabaseClusterCommandRepository.ts)                 │ Removed p_user_id from RPC call                                                                 │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Obstacles validation (app/api/logs/route.ts)                      │ Per-element stressLevel (1–5) and actionResult (AVOIDED/CONFRONTED) validation added            │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ lmConfig optional (LogExperienceUseCase.ts + route.ts)            │ Parameter is now `LMConfig                                                                      │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Typo (chatSystemPrompt.ts)                                        │ introvertion → introversion                                                                     │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Unused imports (app/page.tsx, app/api/persona/route.ts)           │ Removed redirect and PersonaMapper imports                                                      │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ ESLint globs (.eslintrc.json)                                     │ src/core/* → src/core/** etc. (now catches nested files)                                        │
  ├───────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ createdAt (Cluster.ts, query repo, patterns/page.tsx,             │ Added field to ClusterData, mapped from DB, used real value in page; updatedAt made optional    │
  │ types/index.ts)                                                   │                                                                                                 │
  └───────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────┘
"""

# ── Clipboard helpers ─────────────────────────────────────────────────────────

def _clipboard_read() -> str:
    """Read text from the system clipboard (macOS / Linux / Windows)."""
    import platform
    os_name = platform.system()
    try:
        import pyperclip  # type: ignore
        return pyperclip.paste()
    except ImportError:
        pass

    if os_name == "Darwin":
        return subprocess.check_output("pbpaste", env={"LANG": "en_US.UTF-8"}).decode("utf-8")
    elif os_name == "Linux":
        for cmd in (["xclip", "-selection", "clipboard", "-o"],
                    ["xsel", "--clipboard", "--output"],
                    ["wl-paste"]):
            try:
                return subprocess.check_output(cmd).decode("utf-8")
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        raise RuntimeError("No clipboard tool found. Install xclip, xsel, or wl-paste.")
    elif os_name == "Windows":
        return subprocess.check_output(
            ["powershell", "-command", "Get-Clipboard"], text=True
        )
    else:
        raise RuntimeError(f"Unsupported OS: {os_name}")


def _clipboard_write(text: str) -> None:
    """Write text to the system clipboard."""
    import platform
    os_name = platform.system()
    try:
        import pyperclip  # type: ignore
        pyperclip.copy(text)
        return
    except ImportError:
        pass

    if os_name == "Darwin":
        proc = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
        proc.communicate(text.encode("utf-8"))
    elif os_name == "Linux":
        for cmd in (["xclip", "-selection", "clipboard"],
                    ["xsel", "--clipboard", "--input"],
                    ["wl-copy"]):
            try:
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                proc.communicate(text.encode("utf-8"))
                return
            except FileNotFoundError:
                continue
        raise RuntimeError("No clipboard tool found. Install xclip, xsel, or wl-paste.")
    elif os_name == "Windows":
        subprocess.run(
            ["powershell", "-command", f"Set-Clipboard -Value @'\n{text}\n'@"],
            check=True,
        )
    else:
        raise RuntimeError(f"Unsupported OS: {os_name}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--clip" in args:
        # ── clipboard mode ──
        print("📋 Reading from clipboard...", file=sys.stderr)
        text = _clipboard_read()
        if not text.strip():
            print("⚠️  Clipboard is empty.", file=sys.stderr)
            sys.exit(1)

        result = convert(text)
        if not result.strip():
            print("⚠️  No ASCII table found in clipboard content.", file=sys.stderr)
            sys.exit(1)

        _clipboard_write(result)
        print("✅ Converted! Result written back to clipboard.\n", file=sys.stderr)
        print(result)

    elif args and not args[0].startswith("-"):
        # ── file mode ──
        with open(args[0], encoding="utf-8") as f:
            text = f.read()
        print(convert(text))

    else:
        # ── sample mode ──
        print(convert(SAMPLE))
