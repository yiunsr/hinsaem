from __future__ import print_function
#-*- coding: utf-8 -*-

import os
import json
#from pprint import pprint

_config_file_full_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "res", "config.json")
_lib_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = {}
with open(_config_file_full_path, encoding='utf8') as data_file:    
    CONFIG = json.load(data_file)

for key, value in CONFIG.items():
    if "res_" in key:
        CONFIG[key] = os.path.join(_lib_path, value)


CONFIG["sentence_end_mark"] = [".", "!", "?"]
CONFIG["sentence_mark"] = [",", ".", "!", "?"]

#pprint(CONFIG)
