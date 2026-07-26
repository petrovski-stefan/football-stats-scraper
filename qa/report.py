"""Reporting primitive shared by every validator module.

A `Report` collects failures for one labelled subject (one file, or one relationship
between files) and prints a single verdict line. It never raises — `qa/validate.py`
aggregates the booleans and turns them into the process exit code.
"""


class Report:
    """Accumulates failure messages for one subject, then prints a verdict."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.issues: list[str] = []

    def check(self, ok: bool, message: str) -> None:
        """Record `message` as a failure when `ok` is false."""
        if not ok:
            self.issues.append(message)

    @property
    def ok(self) -> bool:
        return not self.issues

    def flush(self) -> bool:
        """Print the verdict and every failure. Returns True when the subject passed."""
        status = "PASS" if self.ok else f"FAIL ({len(self.issues)})"
        print(f"[{status}] {self.label}")
        for issue in self.issues:
            print(f"    - {issue}")
        return self.ok
