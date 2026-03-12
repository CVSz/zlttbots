# path: infrastructure/scripts/devops-fix-permissions.sh
#!/usr/bin/env bash

set -e

ROOT="${1:-.}"

echo "--------------------------------------"
echo "DevOps Script Permission Fixer"
echo "Root directory: $ROOT"
echo "--------------------------------------"

TOTAL=0
FIXED=0
OK=0
WARN=0
CRLF=0

echo ""
echo "Scanning for *.sh files..."
echo ""

FILES=$(find "$ROOT" -type f -name "*.sh")

if [ -z "$FILES" ]; then
    echo "No shell scripts found."
    exit 0
fi

for file in $FILES
do
    TOTAL=$((TOTAL+1))

    # CRLF check
    if file "$file" | grep -q CRLF ; then
        sed -i 's/\r$//' "$file"
        echo "[CRLF FIXED] $file"
        CRLF=$((CRLF+1))
    fi

    # shebang check
    head_line=$(head -n1 "$file")

    if [[ "$head_line" != "#!"* ]]; then
        echo "[WARN] missing shebang -> $file"
        WARN=$((WARN+1))
    fi

    # exec permission
    if [ ! -x "$file" ]; then
        chmod +x "$file"
        echo "[EXEC FIXED] $file"
        FIXED=$((FIXED+1))
    else
        echo "[EXEC OK] $file"
        OK=$((OK+1))
    fi

done

echo ""
echo "------------- SUMMARY -------------"
echo "Scripts found : $TOTAL"
echo "Exec fixed    : $FIXED"
echo "Exec already  : $OK"
echo "CRLF fixed    : $CRLF"
echo "Warnings      : $WARN"
echo "-----------------------------------"
