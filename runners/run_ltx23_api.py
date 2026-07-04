#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LTX-2.3 图生视频运行器
提交工作流到 ComfyUI API，等待完成，下载结果
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import uuid


COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
CLIENT_ID = str(uuid.uuid4())


def upload_image(image_path, image_name):
    """上传图片到 ComfyUI input 目录"""
    import paramiko

    host = os.environ.get("SSH_HOST", "nc1kzw67mzphc18d.ssh.x-gpu.com")
    port = os.environ.get("SSH_PORT", "47424")
    user = os.environ.get("SSH_USER", "root")
    password = os.environ.get("SSH_PASS", "")

    remote_path = f"/root/ComfyUI/input/{image_name}"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=int(port), username=user, password=password, timeout=15)
        sftp = client.open_sftp()
        sftp.put(image_path, remote_path)
        sftp.close()
        print(f"已上传图片: {image_path} -> {remote_path}")
    finally:
        client.close()


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
        print(f"HTTP 错误 {e.code}: {err_body}")
        return None


def check_status(prompt_id):
    """检查工作流状态"""
    try:
        resp = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=15)
        history = json.loads(resp.read().decode("utf-8"))
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            status = history[prompt_id].get("status", {})
            if status.get("completed", False) or outputs:
                return "completed", outputs
            if status.get("status_str") == "error":
                return "error", status
            return "running", {}
        return "pending", {}
    except Exception as e:
        print(f"状态检查异常: {e}")
        return "unknown", {}


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


def download_file(file_info, local_dir):
    """从 ComfyUI 下载文件"""
    filename = file_info["filename"]
    subfolder = file_info.get("subfolder", "")
    file_type = file_info.get("type", "output")

    url = f"{COMFYUI_URL}/view?filename={urllib.parse.quote(filename)}"
    if subfolder:
        url += f"&subfolder={urllib.parse.quote(subfolder)}"
    url += f"&type={file_type}"

    local_path = os.path.join(local_dir, filename)
    resp = urllib.request.urlopen(url, timeout=120)
    with open(local_path, "wb") as f:
        f.write(resp.read())
    print(f"已下载: {local_path} ({os.path.getsize(local_path) / 1024 / 1024:.1f} MB)")
    return local_path


def run_workflow(workflow_path, local_dir=".", poll_interval=10, max_wait=3600):
    """运行工作流并下载结果"""
    print(f"\n{'='*60}")
    print(f"运行工作流: {workflow_path}")
    print(f"{'='*60}")

    prompt_id = submit_workflow(workflow_path)
    if not prompt_id:
        return False

    print(f"等待生成完成 (轮询间隔 {poll_interval}s)...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status, outputs = check_status(prompt_id)
        elapsed = int(time.time() - start_time)
        if status == "completed":
            print(f"\n生成完成! (耗时 {elapsed}s)")
            files = get_output_files(outputs)
            if not files:
                print("警告: 没有找到输出文件")
                return False
            for f_info in files:
                download_file(f_info, local_dir)
            return True
        elif status == "error":
            print(f"\n生成失败: {outputs}")
            return False
        else:
            print(f"  [{elapsed}s] 状态: {status}...", end="\r")
            time.sleep(poll_interval)

    print(f"\n超时 ({max_wait}s)")
    return False


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_dir = os.getcwd()
    assets_dir = os.path.join(project_root, "assets")
    workflows_dir = os.path.join(project_root, "workflows")

    # 确保参考图已上传
    image_path = os.path.join(assets_dir, "beauty_ref.png")
    if os.path.exists(image_path):
        upload_image(image_path, "beauty_ref.png")

    # 运行 5s 版本
    wf_5s = os.path.join(workflows_dir, "ltx23_i2v_beauty_dancing_5s.json")
    if os.path.exists(wf_5s):
        success = run_workflow(wf_5s, local_dir, poll_interval=15, max_wait=1800)
        if not success:
            print("5s 版本生成失败")

    # 运行 10s 版本
    wf_10s = os.path.join(workflows_dir, "ltx23_i2v_beauty_dancing_10s.json")
    if os.path.exists(wf_10s):
        success = run_workflow(wf_10s, local_dir, poll_interval=15, max_wait=3600)
        if not success:
            print("10s 版本生成失败")


if __name__ == "__main__":
    main()
