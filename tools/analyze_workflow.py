#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze ComfyUI workflow JSON files for quick deployment checks."""
import json
import os
import sys
from collections import Counter, defaultdict

MODEL_KEYS = {
    "ckpt_name",
    "unet_name",
    "vae_name",
    "clip_name",
    "text_encoder",
    "lora_name",
    "control_net_name",
    "controlnet_name",
    "upscale_model_name",
    "model_name",
}
IMAGE_KEYS = {"image", "start_image", "end_image", "mask", "video"}
CORE_PREFIXES = (
    "CLIP",
    "VAE",
    "KSampler",
    "Checkpoint",
    "LoadImage",
    "SaveImage",
    "SaveAnimatedWEBP",
    "PreviewImage",
    "UNET",
    "RandomNoise",
    "CFGGuider",
    "Basic",
    "Primitive",
)
KNOWN_CUSTOM_HINTS = {
    "LTX": "ComfyUI-LTXVideo",
    "Wan": "Wan video nodes / ComfyUI native Wan support",
    "VHS": "ComfyUI-VideoHelperSuite",
    "Impact": "ComfyUI-Impact-Pack",
    "ControlNet": "ControlNet nodes",
}


def load_workflow(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def iter_api_nodes(data):
    if not isinstance(data, dict):
        return []
    nodes = []
    for node_id, node in data.items():
        if isinstance(node, dict) and "class_type" in node:
            nodes.append((str(node_id), node["class_type"], node.get("inputs", {})))
    return nodes


def iter_ui_nodes(data):
    nodes = []
    for node in data.get("nodes", []) if isinstance(data, dict) else []:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", "?"))
        node_type = node.get("type", "unknown")
        inputs = {}
        widgets = node.get("widgets_values", [])
        for index, value in enumerate(widgets):
            inputs[f"widget_{index}"] = value
        nodes.append((node_id, node_type, inputs))
    return nodes


def workflow_format(data):
    if iter_api_nodes(data):
        return "api"
    if isinstance(data, dict) and isinstance(data.get("nodes"), list):
        return "ui"
    return "unknown"


def is_file_like(value):
    if not isinstance(value, str):
        return False
    lower = value.lower()
    return lower.endswith((".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".gguf"))


def is_image_like(value):
    if not isinstance(value, str):
        return False
    lower = value.lower()
    return lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".mp4", ".mov", ".gif"))


def collect_from_inputs(inputs):
    models = []
    images = []
    for key, value in inputs.items():
        if isinstance(value, list):
            continue
        if key in MODEL_KEYS or is_file_like(value):
            models.append((key, value))
        if isinstance(value, str) and (key in IMAGE_KEYS or is_image_like(value)):
            images.append((key, value))
    return models, images


def guess_custom_nodes(class_types):
    hints = defaultdict(set)
    for class_type in class_types:
        if class_type.startswith(CORE_PREFIXES):
            continue
        for marker, package in KNOWN_CUSTOM_HINTS.items():
            if marker.lower() in class_type.lower():
                hints[package].add(class_type)
    return hints


def analyze(path):
    data = load_workflow(path)
    fmt = workflow_format(data)
    nodes = iter_api_nodes(data) if fmt == "api" else iter_ui_nodes(data)

    class_counts = Counter(node_type for _, node_type, _ in nodes)
    models = []
    images = []
    outputs = []

    for node_id, node_type, inputs in nodes:
        node_models, node_images = collect_from_inputs(inputs)
        models.extend((node_id, node_type, key, value) for key, value in node_models)
        images.extend((node_id, node_type, key, value) for key, value in node_images)
        if node_type.startswith("Save") or "Output" in node_type:
            outputs.append((node_id, node_type))

    return {
        "path": path,
        "format": fmt,
        "node_count": len(nodes),
        "class_counts": class_counts,
        "models": models,
        "images": images,
        "outputs": outputs,
        "custom_hints": guess_custom_nodes(class_counts.keys()),
    }


def print_section(title):
    print(f"\n{title}")
    print("-" * len(title))


def print_report(report):
    print(f"文件: {report['path']}")
    print(f"格式: {report['format']}")
    print(f"节点数: {report['node_count']}")

    print_section("节点类型")
    for class_type, count in report["class_counts"].most_common():
        print(f"{class_type}: {count}")

    print_section("模型引用")
    if report["models"]:
        for node_id, node_type, key, value in report["models"]:
            print(f"[{node_id}] {node_type}.{key}: {value}")
    else:
        print("未发现明确模型文件引用")

    print_section("输入资源")
    if report["images"]:
        for node_id, node_type, key, value in report["images"]:
            print(f"[{node_id}] {node_type}.{key}: {value}")
    else:
        print("未发现明确图片/视频输入")

    print_section("输出节点")
    if report["outputs"]:
        for node_id, node_type in report["outputs"]:
            print(f"[{node_id}] {node_type}")
    else:
        print("未发现明确输出节点")

    print_section("疑似自定义节点")
    if report["custom_hints"]:
        for package, class_types in report["custom_hints"].items():
            names = ", ".join(sorted(class_types))
            print(f"{package}: {names}")
    else:
        print("未发现明确自定义节点线索")


def main():
    if len(sys.argv) != 2:
        script = os.path.basename(sys.argv[0])
        print(f"用法: python {script} <workflow.json>")
        sys.exit(2)

    try:
        report = analyze(sys.argv[1])
    except Exception as exc:
        print(f"分析失败: {exc}")
        sys.exit(1)
    print_report(report)


if __name__ == "__main__":
    main()
