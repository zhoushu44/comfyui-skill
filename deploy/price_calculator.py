#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI 生成价格计算器
运行指定工作流 3 次，排除首次模型加载时间，计算平均生成时间和单次价格
"""
import json
import sys
import time
import urllib.request
import urllib.error
import uuid
import os

COMFYUI_URL = "http://127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())


def submit_workflow(workflow_path):
    """提交工作流到 ComfyUI"""
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)
    data = json.dumps({"prompt": workflow, "client_id": CLIENT_ID}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))
        if "error" in result:
            print(f"  提交失败: {json.dumps(result, ensure_ascii=False)[:500]}")
            return None
        return result.get("prompt_id")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP 错误 {e.code}: {err[:500]}")
        return None


def wait_for_completion(prompt_id, max_wait=7200):
    """等待工作流完成，返回耗时（秒）"""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = urllib.request.urlopen(
                f"{COMFYUI_URL}/history/{prompt_id}", timeout=15
            )
            history = json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(5)
            continue

        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                return None, status
            if outputs:
                elapsed = time.time() - start
                return elapsed, outputs
        elapsed = int(time.time() - start)
        print(f"\r  生成中... {elapsed}s", end="", flush=True)
        time.sleep(10)
    return None, {"error": "timeout"}


def wait_for_queue_empty():
    """等待队列为空"""
    while True:
        try:
            resp = urllib.request.urlopen(f"{COMFYUI_URL}/queue", timeout=15)
            queue = json.loads(resp.read().decode("utf-8"))
            if not queue.get("queue_running") and not queue.get("queue_pending"):
                return
        except Exception:
            pass
        time.sleep(10)


def run_price_calculation(workflow_path, hourly_rate, runs=3):
    """
    运行价格计算
    :param workflow_path: 工作流文件路径
    :param hourly_rate: 每小时价格（元）
    :param runs: 运行次数（默认 3 次，第 1 次不计时）
    """
    print(f"\n{'='*60}")
    print(f"ComfyUI 生成价格计算器")
    print(f"{'='*60}")
    print(f"工作流: {workflow_path}")
    print(f"每小时价格: {hourly_rate} 元/小时")
    print(f"运行次数: {runs} 次（第 1 次为模型加载，不计时）")
    print(f"{'='*60}\n")

    times = []
    for i in range(1, runs + 1):
        print(f"\n--- 第 {i} 次运行{'（模型加载，不计时）' if i == 1 else ''} ---")
        wait_for_queue_empty()

        prompt_id = submit_workflow(workflow_path)
        if not prompt_id:
            print(f"  第 {i} 次提交失败，跳过")
            continue

        elapsed, outputs = wait_for_completion(prompt_id)
        if elapsed is None:
            print(f"\n  第 {i} 次生成失败: {outputs}")
            continue

        print(f"\n  第 {i} 次耗时: {elapsed:.1f}s ({elapsed/60:.1f}分钟)")
        if i > 1:
            times.append(elapsed)

    if not times:
        print("\n错误: 没有有效的计时结果")
        return

    # 计算统计
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    price_per_video = (avg_time / 3600) * hourly_rate

    print(f"\n{'='*60}")
    print(f"价格计算结果")
    print(f"{'='*60}")
    print(f"有效计时次数: {len(times)} 次（排除第 1 次模型加载）")
    print(f"各次耗时: {', '.join(f'{t:.1f}s' for t in times)}")
    print(f"平均耗时: {avg_time:.1f}s ({avg_time/60:.1f}分钟)")
    print(f"最短耗时: {min_time:.1f}s ({min_time/60:.1f}分钟)")
    print(f"最长耗时: {max_time:.1f}s ({max_time/60:.1f}分钟)")
    print(f"每小时价格: {hourly_rate} 元/小时")
    print(f"单个视频价格: {price_per_video:.4f} 元")
    print(f"  ≈ {price_per_video:.2f} 元/个")
    print(f"{'='*60}")

    # 保存结果
    result = {
        "workflow": workflow_path,
        "hourly_rate": hourly_rate,
        "runs": runs,
        "times": times,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "price_per_video": price_per_video,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    result_path = "/opt/comfyui-adapter/price_result.json"
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {result_path}")

    return result


if __name__ == "__main__":
    workflow_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/wan22_i2v_beauty_dancing_5s.json"
    hourly_rate = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
    runs = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    run_price_calculation(workflow_path, hourly_rate, runs)
