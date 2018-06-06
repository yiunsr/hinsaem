import os
import json
from pprint import pprint

_config_file_full_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "res", "config.json")
_workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = {}
with open(_config_file_full_path, encoding='utf8') as data_file:
    CONFIG = json.load(data_file)

for key, value in CONFIG.items():
    if "res_" in key:
        CONFIG[key] = os.path.join(_workspace_path, value)
    elif "in_" in key:
        CONFIG[key] = os.path.join(_workspace_path, value)


CONFIG["output_path"] = os.path.join(_workspace_path, "output")

# pprint(CONFIG)
