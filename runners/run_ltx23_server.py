#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LTX-2.3 图生视频运行器（服务端）
提交工作流到 ComfyUI API，等待完成，报告输出文件
"""
import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import uuid

COMFYUI_URL = "http://127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())


def submit_workflow(workflow_path):
    """提交工作流到 ComfyUI"""
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    prompt_data = json.dumps({"prompt": workflow, "client_id": CLIENT_ID}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=prompt_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))
        if "error" in result:
            print(f"错误: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return None
        prompt_id = result.get("prompt_id")
        print(f"工作流已提交, prompt_id: {prompt_id}")
        return prompt_id
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP 错误 {e.code}: {err_body[:2000]}")
        return None


def check_status(prompt_id):
    """检查工作流状态"""
    try:
        resp = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=15)
        history = json.loads(resp.read().decode("utf-8"))
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                return "error", status, outputs
            if outputs:
                return "completed", status, outputs
            return "running", status, {}
        return "pending", {}, {}
    except Exception as e:
        print(f"状态检查异常: {e}")
        return "unknown", {}, {}


def get_output_files(outputs):
    """从输出中获取文件信息"""
    files = []
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            for img in node_output["images"]:
                files.append({
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                })
        if "gifs" in node_output:
            for gif in node_output["gifs"]:
                files.append({
                    "filename": gif["filename"],
                    "subfolder": gif.get("subfolder", ""),
                    "type": gif.get("type", "output"),
                })
    return files


def run_workflow(workflow_path, poll_interval=15, max_wait=3600):
    """运行工作流并报告输出文件"""
    print(f"\n{'='*60}")
    print(f"运行工作流: {workflow_path}")
    print(f"{'='*60}")

    prompt_id = submit_workflow(workflow_path)
    if not prompt_id:
        return None

    print(f"等待生成完成 (轮询间隔 {poll_interval}s)...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status, status_info, outputs = check_status(prompt_id)
        elapsed = int(time.time() - start_time)
        if status == "completed":
            print(f"\n生成完成! (耗时 {elapsed}s)")
            files = get_output_files(outputs)
            if not files:
                print("警告: 没有找到输出文件")
                print(f"outputs: {json.dumps(outputs, indent=2, ensure_ascii=False)}")
                return None
            for f_info in files:
                print(f"  输出文件: {f_info['filename']} (subfolder={f_info.get('subfolder','')}, type={f_info.get('type','')})")
            return files
        elif status == "error":
            print(f"\n生成失败: {json.dumps(status_info, indent=2, ensure_ascii=False)}")
            return None
        else:
            print(f"  [{elapsed}s] 状态: {status}...", flush=True)
            time.sleep(poll_interval)

    print(f"\n超时 ({max_wait}s)")
    return None


def main():
    workflow_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ltx23_i2v_beauty_dancing_5s.json"
    poll_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    max_wait = int(sys.argv[3]) if len(sys.argv) > 3 else 1800

    files = run_workflow(workflow_path, poll_interval, max_wait)
    if files:
        print(f"\n输出文件列表:")
        for f in files:
            path = f"/root/ComfyUI/output/{f['filename']}"
            print(f"  {path}")
    else:
        print("未生成输出文件")
        sys.exit(1)


if __name__ == "__main__":
    main()
