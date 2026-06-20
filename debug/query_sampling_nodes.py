#!/usr/bin/env python3
"""Query specific sampling nodes"""
import urllib.request
import json

resp = urllib.request.urlopen("http://127.0.0.1:8188/object_info", timeout=30)
data = json.loads(resp.read().decode("utf-8"))

target_nodes = [
    "RandomNoise",
    "CFGGuider",
    "KSamplerSelect",
    "SamplerCustomAdvanced",
    "VAEDecode",
    "LTXVImgToVideoConditionOnly",
    "LTXVPreprocess",
    "PrimitiveString",
]

for n in target_nodes:
    if n not in data:
        print(f"--- {n} NOT FOUND ---")
        continue
    info = data[n]
    print(f"\n--- {n} ---")
    print(f"category: {info.get('category', '')}")
    if "input" in info:
        inp = info["input"]
        if "required" in inp:
            for k, v in inp["required"].items():
                print(f"  required: {k} = {v}")
        if "optional" in inp:
            for k, v in inp["optional"].items():
                print(f"  optional: {k} = {v}")
    if "output" in info:
        print(f"  output: {info['output']}")
