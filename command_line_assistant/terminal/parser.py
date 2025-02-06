"""..."""

import json
import re

from command_line_assistant.terminal.reader import OUTPUT_FILE_NAME

ANSI_ESCAPE_SEQ = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def parse_terminal_output() -> list[str]:
    result = []
    if not OUTPUT_FILE_NAME.exists():
        return result

    file_contents = OUTPUT_FILE_NAME.read_text()
    file_contents = file_contents.strip().split("\n}\n{")

    # Clean up the blocks and parse them
    for block in file_contents:
        # Add back the curly braces if they were removed in the split
        if not block.startswith("{"):
            block = "{" + block
        if not block.endswith("}"):
            block += "}"

        # Parse the JSON
        try:
            parsed = json.loads(block)
            parsed["command"] = clean_ansi_sequences(parsed["command"])
            parsed["output"] = clean_ansi_sequences(parsed["output"])
            # Just ignore the exit at the end.
            if parsed["output"] == "exit":
                continue
            result.append(parsed)
        except json.JSONDecodeError:
            return result

    return result


def find_output_by_index(index: int, output: list) -> str:
    try:
        return output[index]["output"]
    except (IndexError, KeyError):
        return ""


def clean_ansi_sequences(text: str):
    # Remove ANSI escape sequences
    cleaned_ansi_escape_seq = ANSI_ESCAPE_SEQ.sub("", text)
    return cleaned_ansi_escape_seq.strip()
