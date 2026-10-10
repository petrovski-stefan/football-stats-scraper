#!/usr/bin/env bash
# Scrape every enabled league season in config/leagues.json and rebuild the enriched CSVs.
#
#   1. scrapers.schedule  -> data/archived/raw/<league>_<season>.csv
#   2. scrapers.detail    -> data/archived/raw/<league>_<season>_detail.csv
#   3. scrapers.goals     -> data/archived/raw/goals.csv + data/archived/raw/events.csv
#   4. features.enrich    -> data/archived/processed/<league>_<season>_enriched.csv
#
# The order matters: goals builds its work list from the history match ids that only
# the detail files carry, and enrich joins all three raw outputs.
#
# Run `scripts/pipeline.sh --help` for options.

set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/pipeline.sh [options]

Scrapes every enabled league season in config/leagues.json, then rebuilds data/archived/processed/.

Options:
  --limit N          cap the detail and goals batches at N matches each
  --sections LIST    history sections goals takes ids from (default: home,away,h2h)
  --depth N          matches per history section for goals (default: the scraper's own)
  --skip-schedule    skip stage 1, the league schedule scrape
  --skip-detail      skip stage 2, the match detail pages
  --skip-goals       skip stage 3, the live pages (goals and events)
  -h, --help         show this help

Detail and goals skip matches they have already scraped, so after an interruption
just rerun the same command. Enrich needs no browser and always runs.
EOF
}

log() { printf '%s  %s\n' "$(date +%H:%M:%S)" "$*"; }
die() { printf 'pipeline: %s\n' "$*" >&2; exit 2; }

elapsed() {
  local s=$1
  printf '%dh%02dm%02ds' $((s / 3600)) $((s % 3600 / 60)) $((s % 60))
}

need_value() {
  [[ $# -ge 2 && $2 != --* ]] || die "$1 needs a value"
}

need_positive_int() {
  [[ $2 =~ ^[1-9][0-9]*$ ]] || die "$1 must be a positive integer, got '$2'"
}

# --- arguments ---------------------------------------------------------------

limit_args=()
goals_args=()
run_schedule=1
run_detail=1
run_goals=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit)
      need_value "$@"
      need_positive_int "$1" "$2"
      limit_args=(--limit "$2")
      shift 2
      ;;
    --sections)
      need_value "$@"
      goals_args+=(--sections "$2")
      shift 2
      ;;
    --depth)
      need_value "$@"
      need_positive_int "$1" "$2"
      goals_args+=(--depth "$2")
      shift 2
      ;;
    --skip-schedule) run_schedule=0; shift ;;
    --skip-detail) run_detail=0; shift ;;
    --skip-goals) run_goals=0; shift ;;
    -h | --help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

# --- preconditions -----------------------------------------------------------

# Every data/ and config/ path in the project is relative to the repo root.
cd "$(dirname "${BASH_SOURCE[0]}")/.."

command -v uv >/dev/null || die "uv not found; install it from https://docs.astral.sh/uv/"
[[ -f config/leagues.json ]] \
  || die "config/leagues.json is missing (copy config/leagues.example.json and fill it in)"
# Loading through the scraper's own validator catches a broken config before any page is
# opened, and counts the league seasons stage 1 would actually scrape.
enabled=$(uv run python -c 'from scrapers.links import get_league_seasons as g; print(len(g()))') \
  || die "config/leagues.json is invalid (see the error above)"
[[ $enabled -gt 0 ]] || die "config/leagues.json has no season with \"enabled\": true"

# --- stages ------------------------------------------------------------------

stage=""
trap 'log "FAILED during $stage. Detail and goals are resumable: rerun to continue." >&2' ERR

# run_stage <number> <name> <enabled> <module> [args...]
run_stage() {
  local number=$1 name=$2 enabled=$3 module=$4
  shift 4
  if [[ $enabled -eq 0 ]]; then
    log "[$number/4] $name: skipped"
    return
  fi
  stage=$name
  log "[$number/4] $name: uv run python -m $module${*:+ $*}"
  local start=$SECONDS
  uv run python -m "$module" "$@"
  log "[$number/4] $name: done in $(elapsed $((SECONDS - start)))"
}

# The ${arr[@]+...} form keeps an empty array legal under `set -u` in bash 3.2 (macOS).
run_stage 1 schedule "$run_schedule" scrapers.schedule
run_stage 2 detail "$run_detail" scrapers.detail ${limit_args[@]+"${limit_args[@]}"}
run_stage 3 goals "$run_goals" scrapers.goals \
  ${limit_args[@]+"${limit_args[@]}"} ${goals_args[@]+"${goals_args[@]}"}
run_stage 4 enrich 1 features.enrich

log "pipeline done in $(elapsed "$SECONDS"). Enriched files:"
ls -1 data/archived/processed/*_enriched.csv
