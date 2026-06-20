#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 ComfyUI API 运行 Wan 2.2 i2v 工作流"""
import json
import requests
import time
import uuid
import sys
import os

COMFYUI_URL = "http://127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())

# 提示词
PROMPT = "a beautiful young woman in red dress dancing gracefully, elegant movements, spinning around, fluid motion, high quality, cinematic"
NEG_PROMPT = "blurry, distorted, low quality, static, jittery, deformed, bad anatomy, watermark"

# 模型文件
HIGH_NOISE_MODEL = "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
LOW_NOISE_MODEL = "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
TEXT_ENCODER = "umt5_xxl_fp16.safetensors"
VAE_MODEL = "wan_2.1_vae.safetensors"
CLIP_VISION = "clip_vision_h.safetensors"

def build_workflow(width, height, length, fps, output_prefix):
    """构建 Wan 2.2 i2v API 格式工作流"""
    workflow = {
        # 1. 加载 high noise 模型
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": HIGH_NOISE_MODEL,
                "weight_dtype": "fp8_e4m3fn"
            }
        },
        # 2. 加载 low noise 模型
        "2": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": LOW_NOISE_MODEL,
                "weight_dtype": "fp8_e4m3fn"
            }
        },
        # 3. 加载文本编码器
        "3": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": TEXT_ENCODER,
                "type": "wan"
            }
        },
        # 4. 加载 VAE
        "4": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": VAE_MODEL
            }
        },
        # 5. 加载 CLIP Vision
        "5": {
            "class_type": "CLIPVisionLoader",
            "inputs": {
                "clip_name": CLIP_VISION
            }
        },
        # 6. 加载输入图片
        "6": {
            "class_type": "LoadImage",
            "inputs": {
                "image": "beauty_ref.png"
            }
        },
        # 7. CLIP Vision 编码
        "7": {
            "class_type": "CLIPVisionEncode",
            "inputs": {
                "clip_vision": ["5", 0],
                "image": ["6", 0],
                "crop": "center"
            }
        },
        # 8. 正向提示词
        "8": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": PROMPT,
                "clip": ["3", 0]
            }
        },
        # 9. 负面提示词
        "9": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": NEG_PROMPT,
                "clip": ["3", 0]
            }
        },
        # 10. Wan 图生视频（生成 latent）
        "10": {
            "class_type": "WanImageToVideo",
            "inputs": {
                "positive": ["8", 0],
                "negative": ["9", 0],
                "vae": ["4", 0],
                "width": width,
                "height": height,
                "length": length,
                "batch_size": 1,
                "clip_vision_output": ["7", 0],
                "start_image": ["6", 0]
            }
        },
        # 11. 第一阶段采样（high noise）
        "11": {
            "class_type": "KSampler",
            "inputs": {
                "seed": int(time.time()) % (2**32),
                "steps": 30,
                "cfg": 3.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["10", 0],
                "negative": ["10", 1],
                "latent_image": ["10", 2]
            }
        },
        # 12. 第二阶段采样（low noise）
        "12": {
            "class_type": "KSampler",
            "inputs": {
                "seed": int(time.time()) % (2**32),
                "steps": 20,
                "cfg": 3.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 0.3,
                "model": ["2", 0],
                "positive": ["10", 0],
                "negative": ["10", 1],
                "latent_image": ["11", 0]
            }
        },
        # 13. VAE 解码
        "13": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["12", 0],
                "vae": ["4", 0]
            }
        },
        # 14. 保存为 WEBP 动画
        "14": {
            "class_type": "SaveAnimatedWEBP",
            "inputs": {
                "images": ["13", 0],
                "filename_prefix": output_prefix,
                "fps": fps,
                "lossless": False,
                "quality": 90,
                "method": "default"
            }
        }
    }
    return workflow

def submit_and_wait(workflow, duration_name):
    """提交工作流并等待完成"""
    print(f"\n{'='*60}")
    print(f"提交 Wan 2.2 i2v 工作流: {duration_name}")
    print(f"{'='*60}")
    
    # 提交
    resp = requests.post(f"{COMFYUI_URL}/prompt", json={
        "prompt": workflow,
        "client_id": CLIENT_ID
    })
    
    if resp.status_code != 200:
        print(f"提交失败: {resp.status_code} {resp.text}")
        return None
    
    result = resp.json()
    if "error" in result:
        print(f"工作流错误: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return None
    
    prompt_id = result["prompt_id"]
    print(f"工作流已提交, prompt_id: {prompt_id}")
    
    # 轮询等待完成
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        print(f"\r等待中... {elapsed:.0f}秒", end="", flush=True)
        
        history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
        if prompt_id in history:
            print(f"\n完成! 耗时 {elapsed:.0f}秒")
            outputs = history[prompt_id]["outputs"]
            for node_id, output in outputs.items():
                for img in output.get("images", []):
                    filename = img["filename"]
                    subfolder = img.get("subfolder", "")
                    img_type = img.get("type", "output")
                    print(f"输出文件: {filename} (subfolder: {subfolder}, type: {img_type})")
                    return {
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": img_type
                    }
            # 也检查 gifs
            for node_id, output in outputs.items():
                for img in output.get("gifs", []):
                    filename = img["filename"]
                    subfolder = img.get("subfolder", "")
                    img_type = img.get("type", "output")
                    print(f"输出文件: {filename} (subfolder: {subfolder}, type: {img_type})")
                    return {
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": img_type
                    }
            print("未找到输出文件")
            print(f"outputs: {json.dumps(outputs, indent=2)}")
            return None
        
        # 检查队列状态
        queue = requests.get(f"{COMFYUI_URL}/queue").json()
        queue_running = queue.get("queue_running", [])
        queue_pending = queue.get("queue_pending", [])
        if not queue_running and not queue_pending:
            # 队列空了但 history 里没有，可能是出错了
            time.sleep(2)
            history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
            if prompt_id not in history:
                print(f"\n任务可能失败，队列已空但无结果")
                return None
        
        time.sleep(3)

def download_result(file_info, local_path):
    """下载结果文件"""
    params = {
        "filename": file_info["filename"],
        "subfolder": file_info.get("subfolder", ""),
        "type": file_info.get("type", "output")
    }
    resp = requests.get(f"{COMFYUI_URL}/view", params=params)
    with open(local_path, "wb") as f:
        f.write(resp.content)
    print(f"已下载到: {local_path} ({len(resp.content)} bytes)")

if __name__ == "__main__":
    duration = sys.argv[1] if len(sys.argv) > 1 else "5s"
    
    if duration == "5s":
        width, height, length, fps = 736, 1280, 81, 16
    elif duration == "10s":
        width, height, length, fps = 736, 1280, 161, 16
    else:
        print(f"未知时长: {duration}")
        sys.exit(1)
    
    output_prefix = f"wan22_i2v_beauty_dancing_{duration}"
    
    # 构建并提交工作流
    workflow = build_workflow(width, height, length, fps, output_prefix)
    print(f"参数: {width}x{height}, {length}帧, {fps}fps, 约{length/fps:.1f}秒")
    
    file_info = submit_and_wait(workflow, duration)
    
    if file_info:
        local_path = f"/root/output_{duration}.webp"
        download_result(file_info, local_path)
        print(f"\n{duration} 视频生成完成!")
    else:
        print(f"\n{duration} 视频生成失败!")
        sys.exit(1)
