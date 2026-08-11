#!/bin/bash
# Simple wrapper to run the script with the virtual environment

source .venv/bin/activate
# "$@" forwards flags such as --dry-run; without it they are silently dropped
python edit_german_notes.py "$@"
