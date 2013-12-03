#!/bin/bash

usage() {
  cat <<EOF
Usage: $0 -d DIR -e EXEC [-a ARGS] -o OUTPUT

OPTIONS:
  -h --help  Show this message
  -d --dir   Directory of files to include in the SFX archive
  -e --exec  Script to execute (in the directory)
  -a --args  Arguments to give to the script
  -o --out   Output filename for SFX archive
EOF
}

FILES_DIR=""
EXEC_SCRIPT=""
ARGUMENTS=""
OUTPUT=""
while ! [ -z "$1" ]; do
  case $1 in
    "-h" | "--help")
      usage
      exit 1
      ;;
    "-d" | "--dir")
      shift
      FILES_DIR="$1"
      shift
      ;;
    "-e" | "--exec")
      shift
      EXEC_SCRIPT="$1"
      shift
      ;;
    "-a" | "--args")
      shift
      ARGUMENTS="$1"
      shift
      ;;
    "-o" | "--out*")
      shift
      OUTPUT="$1"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if ! [ -d "$FILES_DIR" ]; then
  echo "Files directory not found" >&2
  exit 3
fi
if ! [ -f "$FILES_DIR/$EXEC_SCRIPT" ]; then
  echo "Exec script not found" >&2
  exit 4
fi
if [ "$OUTPUT" == "" ]; then
  echo "No output file given" >&2
  exit 5
fi

read -r -d '' SCRIPT <<EOF
#!/bin/sh
set -e
TMP=\$(mktemp -d)
tail -n +LINES < \$0 | tar -xz -C \$TMP
set +e
(cd \$TMP; ./$EXEC_SCRIPT $ARGUMENTS)
CODE=$?
set -e
rm -rf \$TMP
exit $CODE
###BINARY_DATA_FOLLOWS###
EOF
LINE=$(($(echo "$SCRIPT" | wc -l)+1))
SCRIPT=$(echo "$SCRIPT" | sed -e "s/+LINES/+$LINE/")
echo "$SCRIPT" > "$OUTPUT"
tar -cz -C "$FILES_DIR" . >> "$OUTPUT"
chmod +x "$OUTPUT"