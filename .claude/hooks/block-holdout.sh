#!/usr/bin/env bash
# Blocks any Bash or PowerShell tool call containing --holdout.
# 2025-26 is spent (notes/RECORD/PREREGISTRATION.md A9); see modelling/CLAUDE.md §2.
# Greps the whole payload (no jq on this machine), so a call whose description mentions
# the flag is blocked too. Fails open if bash is unavailable — see root CLAUDE.md.
payload=$(cat)
if printf '%s' "$payload" | grep -q -- '--holdout'; then
  echo "Blocked: --holdout targets 2025-26, which is spent (notes/RECORD/PREREGISTRATION.md A9). The next confirmatory test needs a new holdout definition: a confirmatory set declared in a dated amendment committed before its scrape starts (A9.2-A9.3, A10). (hook shell: $BASH, bash $BASH_VERSION)" >&2
  exit 2
fi
exit 0
