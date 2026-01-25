#!/usr/bin/env bash
set -euo pipefail

# Configuration
MODE="${1:-build}"
MAX_ITERATIONS="${2:-10}"
ITERATION=0
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Validate mode
if [[ "$MODE" != "plan" && "$MODE" != "build" ]]; then
    echo "Usage: ./loop.sh [plan|build] [max_iterations]"
    exit 1
fi

PROMPT_FILE="$PROJECT_DIR/PROMPT_${MODE}.md"

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: $PROMPT_FILE not found"
    exit 1
fi

echo "Starting Ralph Wiggum loop: mode=$MODE, max_iterations=$MAX_ITERATIONS"

while [[ $ITERATION -lt $MAX_ITERATIONS ]]; do
    ITERATION=$((ITERATION + 1))
    echo ""
    echo "═══════════════════════════════════════════"
    echo " Iteration $ITERATION / $MAX_ITERATIONS (mode: $MODE)"
    echo "═══════════════════════════════════════════"

    # Run Claude Code in headless mode
    claude -p \
        --dangerously-skip-permissions \
        --model opus \
        < "$PROMPT_FILE"

    # Run CI validation (build mode only)
    if [[ "$MODE" == "build" ]]; then
        echo "Running CI validation..."
        if ! "$PROJECT_DIR/scripts/ci.sh"; then
            echo "CI failed - continuing to next iteration to fix"
            continue
        fi
    fi

    # Git commit and push if changes exist
    if [[ -n "$(git status --porcelain)" ]]; then
        git add -A
        git commit -m "Ralph iteration $ITERATION ($MODE): $(date +%Y%m%d-%H%M%S)"
        git push origin "$(git branch --show-current)" || true
    fi

    # Check for completion marker
    if [[ -f "$PROJECT_DIR/IMPLEMENTATION_PLAN.md" ]] && \
       grep -q "STATUS: COMPLETE" "$PROJECT_DIR/IMPLEMENTATION_PLAN.md"; then
        echo ""
        echo "✓ Implementation complete at iteration $ITERATION"
        exit 0
    fi
done

echo ""
echo "Max iterations ($MAX_ITERATIONS) reached"
