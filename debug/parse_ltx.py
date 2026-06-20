#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 LTX-2.3 示例工作流，提取关键信息"""
import json

with open('ltx23_example.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

print("=== 节点类型统计 ===")
node_types = {}
for node in wf["nodes"]:
    t = node["type"]
    node_types[t] = node_types.get(t, 0) + 1

for t, count in sorted(node_types.items()):
    print(f"  {t}: {count}")

print("\n=== 加载器节点（模型加载）===")
for node in wf["nodes"]:
    if "Loader" in node["type"] or "loader" in node["type"]:
        wv = node.get("widgets_values", [])
        print(f"  节点{node['id']} ({node['type']}): {wv}")

print("\n=== 关键参数节点 ===")
for node in wf["nodes"]:
    if node["type"] in ("EmptyLTXVLatentVideo", "LTXVImgToVideo", "LTXVConditioning", "KSampler", "SamplerCustomAdvanced", "SaveAnimatedWEBP", "SaveWEBP", "VHS_VideoCombine"):
        wv = node.get("widgets_values", [])
        print(f"  节点{node['id']} ({node['type']}): {wv}")

print("\n=== models 数组 ===")
if "models" in wf:
    for m in wf["models"]:
        print(f"  {m.get('name', '?')} -> {m.get('directory', '?')}")
else:
    print("  无 models 数组")
