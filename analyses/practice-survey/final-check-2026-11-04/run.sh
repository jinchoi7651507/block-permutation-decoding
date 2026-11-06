#!/bin/bash
cd "$(dirname "$0")"
run() { d=$1; [ -s $d/raw.json ] && return
  (cd $d && env -u ANTHROPIC_DEFAULT_SONNET_MODEL -u ANTHROPIC_DEFAULT_HAIKU_MODEL -u ANTHROPIC_DEFAULT_OPUS_MODEL -u ANTHROPIC_VERTEX_PROJECT_ID -u CLOUD_ML_REGION -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_MESSAGING_TOKEN "$CLAUDE_CODE_EXECPATH" -p --model opus --tools "Read" --allowedTools "Read" --output-format json < PROMPT.txt > raw.json 2> err.txt); }
export -f run
ls -d p1_b* p2_b* | xargs -P 3 -I{} bash -c 'run {}'
echo "done: $(ls */raw.json | wc -l)"
