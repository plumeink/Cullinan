#!/usr/bin/env bash
# Build Cullinan application with Nuitka
# Usage: ./build_nuitka.sh [standalone|onefile]
#
# standalone (default): --standalone mode with separate files
# onefile:              --onefile mode with single binary

set -euo pipefail

MODE="${1:-standalone}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Cullinan Nuitka Build ==="
echo "Mode: ${MODE}"

case "${MODE}" in
    standalone)
        nuitka \
            --standalone \
            --include-package=examples.packaging_demo \
            --include-package=cullinan \
            --enable-plugin=anti-bloat \
            --assume-yes-for-downloads \
            "${SCRIPT_DIR}/main.py"
        echo "=== Build complete: main.dist/main.bin ==="
        ;;
    onefile)
        nuitka \
            --onefile \
            --include-package=examples.packaging_demo \
            --include-package=cullinan \
            --enable-plugin=anti-bloat \
            --assume-yes-for-downloads \
            "${SCRIPT_DIR}/main.py"
        echo "=== Build complete: main.bin ==="
        ;;
    *)
        echo "Error: unknown mode '${MODE}'. Use 'standalone' or 'onefile'."
        exit 1
        ;;
esac
