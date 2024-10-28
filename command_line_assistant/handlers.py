import json
import logging
import os

import requests

from command_line_assistant.utils import get_payload


def _handle_history_read(config: dict) -> dict:
    """
    Reads the history from a file and returns it as a list of dictionaries.
    """
    if not config.get("enabled", False):
        return []

    filepath = config.get("filepath", "/tmp/command-line-assistant_history.json")
    if not filepath or not os.path.exists(filepath):
        logging.warning(f"History file {filepath} does not exist.")
        logging.warning("File will be created with first response.")
        return []

    max_size = config.get("max_size", 100)
    history = []
    try:
        with open(filepath, "r") as f:
            history = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to read history file {filepath}: {e}")
        return []

    logging.info(f"Taking maximum of {max_size} entries from history.")
    return history[:max_size]


def handle_history_write(config: dict, history: list, response: str) -> None:
    """
    Writes the history to a file.
    """
    if not config.get("enabled", False):
        return
    filepath = config.get("filepath", "/tmp/command-line-assistant_history.json")
    if response:
        history.append({"role": "assistant", "content": response})
    try:
        with open(filepath, "w") as f:
            json.dump(history, f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to write history file {filepath}: {e}")


def handle_script_session(command_line_assistant_tmp_file) -> None:
    """
    Starts a 'script' session and writes the PID to a file, but leaves control of the terminal to the user.
    """
    # Prepare the script command
    script_command = ["script", "-f", command_line_assistant_tmp_file]

    # Start the script session and leave control to the terminal
    os.system(" ".join(script_command))

    # Remove the captured output after the script session ends
    if os.path.exists(command_line_assistant_tmp_file):
        logging.info(f"Removing {command_line_assistant_tmp_file}")
        os.remove(command_line_assistant_tmp_file)


def _handle_caret(query: str, config: dict) -> str:
    """
    Replaces caret (^) with command output specified in config file.
    """
    if "^" not in query:
        return query

    output_capture_settings = config.get("output_capture_settings", {})
    captured_output_file = output_capture_settings.get(
        "captured_output_file", "/tmp/command-line-assistant_output.txt"
    )

    if not os.path.exists(captured_output_file):
        logging.error(
            f"Output file {captured_output_file} does not exist, change location of file in config to use '^'."
        )
        exit(1)

    prompt_separator = output_capture_settings.get("prompt_separator", "$")
    with open(captured_output_file, "r") as f:
        # NOTE: takes only last command + output from file
        output = f.read().split(prompt_separator)[-1].strip()
    query = query.replace("^", "")
    query = f"Context data: {output}\nQuestion: " + query
    return query


def handle_query(query: str, config: dict) -> None:
    query = _handle_caret(query, config)
    # NOTE: Add more query handling here

    logging.info(f"Query: {query}")

    backend_service = config.get("backend_service", {})
    query_endpoint = backend_service.get(
        "query_endpoint", "http://0.0.0.0:8080/v1/query/"
    )

    try:
        history_conf = config.get("history", {})
        history = _handle_history_read(history_conf)
        payload = get_payload(query)
        logging.info("Waiting for response from AI...")
        response = requests.post(
            query_endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30,  # waiting for more than 30 seconds does not make sense
        )
        response.raise_for_status()
        completion = response.json()
        response_data = completion.get("response", {})
        references = completion.get("referenced_documents", {})
        references = [
            f'{reference["title"]}: {reference["docs_url"]}' for reference in references
        ]
        references_str = (
            "\n\nReferences:\n" + "\n".join(references) if references else ""
        )
        handle_history_write(
            history_conf,
            [
                *history,
                {"role": "user", "content": query},
            ],
            response_data,
        )
        print(response_data + references_str)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get response from AI: {e}")
        exit(1)
