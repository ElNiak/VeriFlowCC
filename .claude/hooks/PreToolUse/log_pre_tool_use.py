#!/usr/bin/env python3

import json
import random
import string
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Each tool use is logged in a separate file with a unique timestamped name.
# Log files are stored in a dedicated 'tool_logs' directory for concurrency safety.


def main():
    try:
        # Read input data from stdin
        input_data = json.load(sys.stdin)

        # Extract tool_input from the input data
        tool_input = input_data.get("tool_input", {})

        # Create log entry with timestamp
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": input_data.get("session_id"),
            "tool_name": input_data.get("tool_name"),
            "command": tool_input.get("command"),
            "description": tool_input.get("description"),
        }

        # Directory for per-tool-use logs
        logs_dir = Path(__file__).parent.parent / "tool_logs"
        try:
            logs_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Error creating log directory {logs_dir}: {e}", file=sys.stderr)
            sys.exit(1)

        # Generate unique filename: toolname_YYYY-MM-DDTHH-MM-SS-micro_UUID.json
        now = datetime.now().isoformat().replace(":", "-")
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        tool = input_data.get("tool_name", "tool")
        filename = f"{now}_{tool}_{rand}.json"
        log_path = logs_dir / filename

        # Write log entry atomically
        tmp_path = log_path.with_suffix(".tmp")
        try:
            with tmp_path.open("w") as f:
                json.dump(log_entry, f, indent=2)
            # Atomic move
            tmp_path.replace(log_path)
        except Exception as e:
            print(f"Error writing log file {log_path}: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)

        print(f"Tool input logged to {log_path}")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


main()
