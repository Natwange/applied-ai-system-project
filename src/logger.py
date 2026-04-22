import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_log_path = os.path.join(LOG_DIR, f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

_logger = logging.getLogger("vibefinder")
_logger.setLevel(logging.DEBUG)

_fmt = logging.Formatter("[%(asctime)s] [%(levelname)-8s] %(message)s", datefmt="%H:%M:%S")

_file_handler = logging.FileHandler(_log_path, encoding="utf-8")
_file_handler.setFormatter(_fmt)
_logger.addHandler(_file_handler)


def _log(tag: str, message: str, level: str = "info") -> None:
    line = f"[{tag}] {message}"
    getattr(_logger, level)(line)
    print(line)


def log_session_start(mode_label: str) -> None:
    _log("SESSION", f"Started — scoring mode: {mode_label}")


def log_tool_call(tool_name: str, result_summary: str = "") -> None:
    msg = f"{tool_name}()"
    if result_summary:
        msg += f" → {result_summary}"
    _log("TOOL", msg)


def log_agent_plan(tools: list[str]) -> None:
    _log("AGENT", f"Planning next actions: {', '.join(tools)}")


def log_feedback(raw: str) -> None:
    _log("FEEDBACK", f'received: "{raw}"')


def log_conflicts(conflicts: list[str]) -> None:
    for c in conflicts:
        _log("CONFLICT", c, level="warning")


def log_profile_updates(changes: list[str]) -> None:
    if not changes:
        _log("PROFILE", "No changes detected from feedback.")
        return
    for change in changes:
        _log("PROFILE", change)


def log_round_complete(round_num: int, top_score: float) -> None:
    _log("ROUND", f"Round {round_num} complete — top score: {top_score:.2f}")


def log_mode_switch(old_label: str, new_label: str) -> None:
    _log("MODE", f"Switched: {old_label} → {new_label}")


def log_guardrail(message: str) -> None:
    _log("GUARDRAIL", message, level="warning")


def log_session_end(rounds: int) -> None:
    _log("SESSION", f"Ended after {rounds} round(s). Log saved to {_log_path}")
