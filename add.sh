#!/bin/bash
# Wrapper script to run add_word.py in virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ANKICONNECT_URL="http://127.0.0.1:8765"

anki_connect_up() {
    curl -s -m 1 -o /dev/null "$ANKICONNECT_URL"
}

if ! anki_connect_up; then
    echo "Anki is not running, starting it..."
    nohup anki >/dev/null 2>&1 &
    disown

    echo -n "Waiting for AnkiConnect to become available..."
    for i in $(seq 1 30); do
        if anki_connect_up; then
            echo " ready."
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    if ! anki_connect_up; then
        echo "Warning: AnkiConnect did not become available after starting Anki." >&2
        echo "Make sure Anki is installed and the AnkiConnect add-on is enabled." >&2
    fi
fi

source "$SCRIPT_DIR/.venv/bin/activate"
python "$SCRIPT_DIR/add_word.py" "$@"
