"""Raw run records: a study saves what it printed to `notes/runs/<date>_<name>.txt`.

`modelling/CLAUDE.md` §2: any run that reads outcome labels saves its raw output there.
Only the raw transcript is written; the findings are written by hand in static notes.
"""

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager, redirect_stdout
from datetime import date
from typing import TextIO, cast

RUNS_DIR = os.path.join("notes", "runs")


class _Tee:
    """Sends every write to the terminal and to the run file."""

    def __init__(self, *streams: TextIO) -> None:
        self._streams = streams

    def write(self, text: str) -> int:
        for stream in self._streams:
            stream.write(text)
        return len(text)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


@contextmanager
def recorded(name: str) -> Generator[str]:
    """Copy stdout into `notes/runs/<today>_<name>.txt` (UTF-8) while the block runs.

    A failed run keeps its transcript too. A rerun on the same day overwrites that day's file.
    """
    os.makedirs(RUNS_DIR, exist_ok=True)
    path = os.path.join(RUNS_DIR, f"{date.today().isoformat()}_{name}.txt")
    try:
        with (
            open(path, "w", encoding="utf-8") as fh,
            redirect_stdout(cast(TextIO, _Tee(sys.stdout, fh))),
        ):
            yield path
    finally:
        print(f"\nwrote {path}")
