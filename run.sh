#!/bin/bash
# run.sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

export PATH="$DIR/bin:$PATH"
exec ./venv/bin/python main.py
