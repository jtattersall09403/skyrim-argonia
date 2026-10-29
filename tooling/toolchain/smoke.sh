#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PATH="$HOME/.argonia/venv/bin:$HOME/.dotnet:$HOME/.dotnet/tools:$HOME/.local/bin:$PATH" DOTNET_ROOT="$HOME/.dotnet" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
echo "python   $(python3 --version)"
echo "pytest   $(pytest --version 2>&1 | head -1)"
echo "ruff     $(ruff --version)"
echo "dotnet   $(dotnet --version)"
echo "spriggit $(ls "$HOME/.argonia/spriggit")  $(test -x "$HOME/.local/bin/spriggit" && echo installed)"
echo "rtk      $(rtk --version)"
echo "jq       $(jq --version)"
dotnet run --project "$ROOT/tools/ArgoniaGen" -c Release -- counts --data "${ARGONIA_DATA:-$HOME/games/skyrimse/Data}"
echo "smoke ok"
