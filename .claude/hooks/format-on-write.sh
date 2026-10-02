#!/usr/bin/env bash
# PostToolUse hook on Edit/Write: converts the file Claude just wrote to CRLF and formats it
# the way VS Code does on save, so a Ctrl+S afterwards changes nothing. .py: ruff (import
# sort, then format; ruff keeps the CRLF).
# .md: the Prettier copy inside the VS Code extension, with .prettierrc; .prettierignore
# skips notes/. Files outside the repo are skipped. No jq here, so node reads the payload.
# Exit 2 shows the error to Claude; the edit itself has already happened.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
rel=$(node -e '
  let s = "";
  process.stdin.on("data", (d) => (s += d)).on("end", () => {
    const f = JSON.parse(s).tool_input?.file_path ?? "";
    const r = f ? path.relative(process.cwd(), f) : "";
    if (r && !r.startsWith("..") && !path.isAbsolute(r)) process.stdout.write(r);
  });
')
case "$rel" in
  '' | *.sh) exit 0 ;; # outside the repo, or a shell script (stays LF, see .gitattributes)
esac
unix2dos -q "$rel" # CRLF on disk is the repo default; Write creates LF files
prettier=$(ls -d ~/.vscode/extensions/esbenp.prettier-vscode-*/node_modules/prettier/bin/prettier.cjs 2>/dev/null | sort -V | tail -1)
case "$rel" in
  *.py) out=$(uv run --quiet ruff check --quiet --select I --fix "$rel" 2>&1 &&
    uv run --quiet ruff format --quiet "$rel" 2>&1) ;;
  *.md) out=$(node "$prettier" --write --log-level warn "$rel" 2>&1) ;;
  *) exit 0 ;;
esac || {
  printf 'format-on-write: %s was not formatted:\n%s\n' "$rel" "$out" >&2
  exit 2
}
