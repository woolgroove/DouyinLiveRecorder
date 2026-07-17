import os
import re
import shlex
from collections.abc import Callable


POSITIONAL_SCRIPT_EXTENSIONS = ('.bat', '.cmd', '.ps1', '.sh', '.vbs')
PYTHON_EXECUTABLE_PATTERN = re.compile(r'^(?:pythonw?(?:\d+(?:\.\d+)*)?|py)(?:\.exe)?$', re.IGNORECASE)


def _command_name(token: str) -> str:
    return token.strip('"\'').replace('\\', '/').rsplit('/', maxsplit=1)[-1]


def has_recording_output(
    save_file_path: str,
    split: bool,
    list_files: Callable[[str], list[str]] | None = None,
) -> bool:
    """判断录制是否已落盘。主播断流时 ffmpeg 常非 0 退出,不能仅靠返回码判断。"""
    if split:
        directory = os.path.dirname(save_file_path) or '.'
        prefix = os.path.basename(save_file_path).rsplit('_', maxsplit=1)[0]
        if not os.path.isdir(directory):
            return False
        files = list_files(directory) if list_files else [
            os.path.join(root, name)
            for root, _, names in os.walk(directory)
            for name in names
        ]
        return any(
            prefix in os.path.basename(path) and os.path.isfile(path) and os.path.getsize(path) > 0
            for path in files
        )
    return os.path.isfile(save_file_path) and os.path.getsize(save_file_path) > 0


def is_offline_timeout_reached(offline_since: float | None, monitor_timeout: int, now: float) -> bool:
    return offline_since is not None and now - offline_since >= monitor_timeout


def get_offline_wait_seconds(
    poll_interval: int,
    monitor_timeout: int,
    offline_since: float | None,
    now: float,
) -> int:
    """下线计时进行中时,将轮询等待限制在剩余超时时间内。"""
    if offline_since is None:
        return max(0, poll_interval)
    remaining = max(0, monitor_timeout - (now - offline_since))
    return min(max(0, poll_interval), int(remaining + 0.999))


def build_script_command(command: str, python_params: list[str], positional_params: list[str]) -> str:
    command = command.strip()
    try:
        tokens = shlex.split(command, posix=False)
    except ValueError:
        tokens = []

    params = []
    if tokens:
        command_name = _command_name(tokens[0])
        command_name_lower = command_name.lower()
        if command_name_lower.endswith('.py') or PYTHON_EXECUTABLE_PATTERN.fullmatch(command_name):
            params = python_params
        elif command_name_lower.endswith(POSITIONAL_SCRIPT_EXTENSIONS):
            params = positional_params
        elif any(_command_name(token).lower().endswith('.py') for token in tokens[1:]):
            params = python_params
        elif any(
            _command_name(token).lower().endswith(POSITIONAL_SCRIPT_EXTENSIONS)
            for token in tokens[1:]
        ):
            params = positional_params

    return command + (' ' + ' '.join(params) if params else '')
