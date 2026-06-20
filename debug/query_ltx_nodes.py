#!/usr/bin/env python3
"""Query specific LTX nodes and save to file"""
import urllib.request
import json

resp = urllib.request.urlopen("http://127.0.0.1:8188/object_info", timeout=30)
data = json.loads(resp.read().decode("utf-8"))

# Query specific nodes we need for LTX-2.3 i2v
target_nodes = [
    "CheckpointLoaderSimple",
    "CLIPLoader",
    "LTXVLLaVAConditioning",
    "LTXVConditioning",
    "LTXVLoader",
    "LTXVDecode",
    "LTXVScheduler",
    "LTXVImgToVideo",
    "EmptyLTXVLatentImage",
    "VAELoader",
    "LoadImage",
    "CLIPTextEncode",
    "KSampler",
    "LTXVScheduler",
    "SaveAnimatedWEBP",
    "VHS_VideoCombine",
]

# Find all LTX nodes
ltx_nodes = sorted([k for k in data if "LTX" in k or "ltx" in k.lower()])
print("=== ALL LTX nodes ===")
for n in ltx_nodes:
    print(n)

print("\n\n=== Detailed node info ===")
for n in ltx_nodes + [x for x in target_nodes if x in data]:
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
