#!/bin/bash
set -e
DEPOTTOOLS=$1
OUTDIR=$2

BASEDIR=$(dirname "$0")
INPUT="$BASEDIR/chrome_gpu_triage.json"
SCRIPT="$BASEDIR/issue_counter.py"
mkdir -p "$OUTDIR"
OUTFILE="$OUTDIR/$(date "+%Y-%m-%d-%H:%M").json"

PYTHONPATH=$DEPOTTOOLS python "$SCRIPT" --file "$INPUT" --output_file="$OUTFILE"

git init "$OUTDIR"
(cd $OUTDIR; git add *.json;git commit -a -m "Autocommit"; git push 2>/dev/null)
