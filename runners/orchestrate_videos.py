#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成编排脚本（服务端）
依次运行: Wan 2.2 5s -> Wan 2.2 10s -> LTX-2.3 5s -> LTX-2.3 10s
等待当前任务完成后再提交下一个
"""
import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import uuid
import os

COMFYUI_URL = "http://127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())

# 工作流文件列表（按顺序执行）
WORKFLOWS = [
    ("Wan 2.2 5s", "/tmp/wan22_i2v_beauty_dancing_5s.json"),
    ("Wan 2.2 10s", "/tmp/wan22_i2v_beauty_dancing_10s.json"),
    ("LTX-2.3 5s", "/tmp/ltx23_i2v_beauty_dancing_5s.json"),
    ("LTX-2.3 10s", "/tmp/ltx23_i2v_beauty_dancing_10s.json"),
]

# 结果记录文件
RESULTS_FILE = "/tmp/video_generation_results.json"


def api_get(path):
    """GET 请求"""
    try:
        resp = urllib.request.urlopen(f"{COMFYUI_URL}{path}", timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"API GET 错误 ({path}): {e}")
        return None


def api_post(path, data):
    """POST 请求"""
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{COMFYUI_URL}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"API POST HTTP 错误 {e.code}: {err[:2000]}")
        return {"error": err}
    except Exception as e:
        print(f"API POST 错误: {e}")
        return {"error": str(e)}


def wait_for_queue_empty():
    """等待队列为空（当前任务完成）"""
    print("等待当前队列任务完成...")
    while True:
        queue = api_get("/queue")
        if queue is None:
            print("无法获取队列状态，等待 10s 后重试...")
            time.sleep(10)
            continue
        running = queue.get("queue_running", [])
        pending = queue.get("queue_pending", [])
        if not running and not pending:
            print("队列已空")
            return True
        # 显示当前运行的任务
        if running:
            task_id = running[0][1] if len(running[0]) > 1 else "?"
            print(f"  队列: {len(running)} 运行中, {len(pending)} 等待中 (当前: {task_id[:12]}...)", flush=True)
        time.sleep(15)


def submit_workflow(workflow_path):
    """提交工作流"""
    if not os.path.exists(workflow_path):
        print(f"工作流文件不存在: {workflow_path}")
        return None

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    result = api_post("/prompt", {"prompt": workflow, "client_id": CLIENT_ID})
    if "error" in result:
        print(f"提交失败: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        return None

    prompt_id = result.get("prompt_id")
    print(f"已提交, prompt_id: {prompt_id}")
    return prompt_id


def wait_for_completion(prompt_id, max_wait=7200, poll_interval=15):
    """等待工作流完成"""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        history = api_get(f"/history/{prompt_id}")
        if history and prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                print(f"\n生成失败: {json.dumps(status, indent=2, ensure_ascii=False)}")
                return None, status
            if outputs:
                elapsed = int(time.time() - start_time)
                print(f"\n完成! (耗时 {elapsed}s)")
                return outputs, status
            # 有 history 但没有 outputs，可能还在运行
        elapsed = int(time.time() - start_time)
        print(f"  [{elapsed}s] 等待中...", flush=True)
        time.sleep(poll_interval)

    print(f"\n超时 ({max_wait}s)")
    return None, {"status_str": "timeout"}


def extract_output_files(outputs):
    """提取输出文件信息"""
    files = []
    for node_id, node_output in outputs.items():
        for img in node_output.get("images", []):
            files.append({
                "filename": img["filename"],
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output"),
            })
        for gif in node_output.get("gifs", []):
            files.append({
                "filename": gif["filename"],
                "subfolder": gif.get("subfolder", ""),
                "type": gif.get("type", "output"),
            })
    return files


def check_running_task():
    """检查当前是否有正在运行的任务，如果有则返回其 prompt_id"""
    queue = api_get("/queue")
    if queue is None:
        return None
    running = queue.get("queue_running", [])
    if running and len(running[0]) > 1:
        return running[0][1]
    return None


def main():
    results = {}

    # 加载已有结果（如果脚本中途重启）
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            results = json.load(f)
        print(f"已加载 {len(results)} 个已完成的结果")

    # 检查是否有正在运行的任务（可能是之前手动提交的）
    running_id = check_running_task()
    if running_id and "Wan 2.2 5s" not in results:
        print(f"\n检测到正在运行的任务: {running_id}")
        print("等待该任务完成并记录结果...")
        outputs, status = wait_for_completion(running_id, max_wait=7200, poll_interval=15)
        if outputs:
            files = extract_output_files(outputs)
            if files:
                results["Wan 2.2 5s"] = {
                    "status": "completed",
                    "prompt_id": running_id,
                    "files": files,
                    "note": "从正在运行的任务中捕获"
                }
                for f_info in files:
                    print(f"  输出: /root/ComfyUI/output/{f_info['filename']}")
        else:
            results["Wan 2.2 5s"] = {
                "status": "failed",
                "prompt_id": running_id,
                "error": str(status)[:500],
            }
        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    for name, workflow_path in WORKFLOWS:
        if name in results:
            print(f"\n{'='*60}")
            print(f"跳过已完成: {name}")
            r = results[name]
            if "files" in r:
                for f in r["files"]:
                    print(f"  输出: /root/ComfyUI/output/{f['filename']}")
            else:
                print(f"  状态: {r.get('status', 'unknown')}")
            continue

        print(f"\n{'='*60}")
        print(f"开始处理: {name}")
        print(f"工作流: {workflow_path}")
        print(f"{'='*60}")

        # 等待队列空闲
        wait_for_queue_empty()

        # 提交工作流
        prompt_id = submit_workflow(workflow_path)
        if not prompt_id:
            results[name] = {"status": "submit_failed"}
            with open(RESULTS_FILE, "w") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            continue

        # 等待完成
        outputs, status = wait_for_completion(prompt_id, max_wait=7200, poll_interval=15)
        if outputs:
            files = extract_output_files(outputs)
            if files:
                results[name] = {
                    "status": "completed",
                    "prompt_id": prompt_id,
                    "files": files,
                }
                for f_info in files:
                    filepath = f"/root/ComfyUI/output/{f_info['filename']}"
                    print(f"  输出: {filepath}")
            else:
                results[name] = {
                    "status": "no_output",
                    "prompt_id": prompt_id,
                    "outputs": str(outputs)[:500],
                }
        else:
            results[name] = {
                "status": "failed",
                "prompt_id": prompt_id,
                "error": str(status)[:500],
            }

        # 保存结果
        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"结果已保存到 {RESULTS_FILE}")

    # 打印最终结果
    print(f"\n{'='*60}")
    print("所有任务完成! 最终结果:")
    print(f"{'='*60}")
    for name, result in results.items():
        status = result.get("status", "unknown")
        print(f"  {name}: {status}")
        if "files" in result:
            for f in result["files"]:
                print(f"    -> /root/ComfyUI/output/{f['filename']}")


if __name__ == "__main__":
    main()
