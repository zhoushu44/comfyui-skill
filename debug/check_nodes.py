#!/usr/bin/env python3
"""检查节点定义"""
import json
import requests

COMFYUI_URL = "http://127.0.0.1:8188"

# 检查 CLIPVisionEncode
resp = requests.get(f"{COMFYUI_URL}/object_info/CLIPVisionEncode")
data = resp.json()
print("=== CLIPVisionEncode ===")
print(json.dumps(data["CLIPVisionEncode"]["input"], indent=2))

# 检查 WanImageToVideo
resp = requests.get(f"{COMFYUI_URL}/object_info/WanImageToVideo")
data = resp.json()
print("\n=== WanImageToVideo ===")
print(json.dumps(data["WanImageToVideo"]["input"], indent=2))

# 检查 KSampler
resp = requests.get(f"{COMFYUI_URL}/object_info/KSampler")
data = resp.json()
print("\n=== KSampler ===")
print(json.dumps(data["KSampler"]["input"], indent=2))
