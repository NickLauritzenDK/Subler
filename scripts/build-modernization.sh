#!/bin/bash
# Compatibility entry point; the Neo recipe is maintained in build-neo.sh.
set -euo pipefail
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/build-neo.sh" "$@"
