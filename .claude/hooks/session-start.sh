#!/bin/bash
# Claude Code 웹 세션 시작 시 skbuild 와 테스트 의존성을 설치한다.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"
python3 -m pip install --quiet --disable-pip-version-check -e ".[test]"
