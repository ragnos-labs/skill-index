"""Execute one explicit command without a shell; used by generated launchers."""
import datetime
import json
import subprocess
from pathlib import Path


def run(config, execute=subprocess.run):
    print('Checked:', datetime.datetime.now().astimezone().isoformat(), flush=True)
    print(config['title'], flush=True)
    try:
        result = execute(config['argv'], cwd=config['cwd'], timeout=config['timeout'],
                         shell=False, check=False)
    except subprocess.TimeoutExpired:
        print('Unavailable: command timed out.', flush=True)
        return 124
    except OSError as exc:
        print('Unavailable:', type(exc).__name__, flush=True)
        return 127
    print('Command exit:', result.returncode, flush=True)
    return result.returncode


def main(config_path):
    try:
        config = json.loads(Path(config_path).read_text())
        return run(config)
    except (ValueError, KeyError, TypeError):
        print('Unavailable: invalid command configuration.', flush=True)
        return 2


def json_object(result):
    """A failed probe or malformed payload is unavailable, never a healthy empty state."""
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
        return value if isinstance(value, dict) else None
    except (ValueError, TypeError):
        return None


def display_state(result, name_fragment):
    value = json_object(result)
    if value is None or not isinstance(value.get('SPDisplaysDataType'), list):
        return 'unavailable'
    displays = []
    for group in value['SPDisplaysDataType']:
        if not isinstance(group, dict) or not isinstance(group.get('spdisplays_ndrvs', []), list):
            return 'unavailable'
        for item in group.get('spdisplays_ndrvs', []):
            if not isinstance(item, dict) or not isinstance(item.get('_name', ''), str):
                return 'unavailable'
            if name_fragment.lower() in item.get('_name', '').lower(): displays.append(item)
    return 'online' if any(d.get('spdisplays_online') == 'spdisplays_yes' for d in displays) else 'not active'
