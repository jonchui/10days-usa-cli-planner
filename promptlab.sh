#!/usr/bin/env bash
# One-command entry point for PromptLab.
#
#   ./promptlab.sh                                  # 5 prompts, claude/opus
#   ./promptlab.sh --dry-run                        # free offline smoke test
#   ./promptlab.sh --backend codex --model gpt-5    # same run on Codex credits
#   ./promptlab.sh promptlab/prompts/ten-days-strategy.toml
#
# Requires: python3.11+ and a CLI you are already logged into (`claude` or `codex`).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found on PATH" >&2
  exit 1
fi

python3 - <<'EOF' || { echo "PromptLab needs Python 3.11+ (tomllib)" >&2; exit 1; }
import sys
sys.exit(0 if sys.version_info >= (3, 11) else 1)
EOF

exec python3 -m promptlab "$@"
