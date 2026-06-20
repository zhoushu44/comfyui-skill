#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LTX-2.3 图生视频 API 格式工作流生成器
生成 5s 和 10s 版本，736×1280 分辨率
"""
import json
import random
import sys


def build_ltx23_i2v_workflow(
    prompt: str,
    negative_prompt: str,
    image_name: str,
    width: int = 736,
    height: int = 1280,
    length: int = 121,  # ~5s @ 25fps
    steps: int = 30,
    cfg: float = 3.0,
    fps: float = 25.0,
    seed: int = None,
    filename_prefix: str = "ltx23_i2v_beauty_dancing_5s",
):
    """构建 LTX-2.3 i2v API 格式工作流"""
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    workflow = {
        # 1. 加载 checkpoint (ltx-2.3-22b-distilled)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "ltx-2.3-22b-distilled.safetensors"
            }
        },
        # 2. 加载文本编码器 (Gemma-3 12B FP4)
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it_fp4_mixed.safetensors",
                "ckpt_name": "ltx-2.3-22b-distilled.safetensors",
                "device": "default"
            }
        },
        # 3. 加载蒸馏 LoRA
        "3": {
            "class_type": "LTX2LoraLoaderAdvanced",
            "inputs": {
                "lora_name": "ltxv/ltx-2.3-22b-distilled-lora-384-1.1.safetensors",
                "model": ["1", 0],
                "strength_model": 1.0,
                "video": 1.0,
                "video_to_audio": 1.0,
                "audio": 1.0,
                "audio_to_video": 1.0,
                "other": 1.0
            }
        },
        # 4. 正向提示词编码
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["2", 0]
            }
        },
        # 5. 负向提示词编码
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt,
                "clip": ["2", 0]
            }
        },
        # 6. 加载参考图片
        "6": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_name
            }
        },
        # 7. 图生视频条件 + 潜空间
        "7": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["4", 0],
                "negative": ["5", 0],
                "vae": ["1", 2],
                "image": ["6", 0],
                "width": width,
                "height": height,
                "length": length,
                "batch_size": 1,
                "strength": 1.0
            }
        },
        # 8. 设置帧率
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["7", 0],
                "negative": ["7", 1],
                "frame_rate": fps
            }
        },
        # 9. LTXV 调度器 (生成 sigmas)
        "9": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": steps,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["7", 2]
            }
        },
        # 10. 随机噪声
        "10": {
            "class_type": "RandomNoise",
            "inputs": {
                "noise_seed": seed
            }
        },
        # 11. CFG 引导器
        "11": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["8", 0],
                "negative": ["8", 1],
                "cfg": cfg
            }
        },
        # 12. 采样器选择
        "12": {
            "class_type": "KSamplerSelect",
            "inputs": {
                "sampler_name": "euler"
            }
        },
        # 13. 高级自定义采样
        "13": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["10", 0],
                "guider": ["11", 0],
                "sampler": ["12", 0],
                "sigmas": ["9", 0],
                "latent_image": ["7", 2]
            }
        },
        # 14. VAE 解码
        "14": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["13", 0],
                "vae": ["1", 2]
            }
        },
        # 15. 保存为动画 WEBP
        "15": {
            "class_type": "SaveAnimatedWEBP",
            "inputs": {
                "images": ["14", 0],
                "filename_prefix": filename_prefix,
                "fps": fps,
                "lossless": False,
                "quality": 90,
                "method": "default"
            }
        }
    }
    return workflow


def main():
    prompt = "a beautiful young woman in red dress dancing gracefully, elegant movements, spinning around, fluid motion, high quality, cinematic"
    negative_prompt = "blurry, distorted, low quality, static, jittery, deformed, bad anatomy, watermark, worst quality"
    image_name = "beauty_ref.png"

    # 5s 版本: 121 帧 @ 25fps ≈ 4.84s
    wf_5s = build_ltx23_i2v_workflow(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image_name=image_name,
        width=736,
        height=1280,
        length=121,
        steps=30,
        cfg=3.0,
        fps=25.0,
        filename_prefix="ltx23_i2v_beauty_dancing_5s"
    )

    # 10s 版本: 241 帧 @ 25fps ≈ 9.64s
    wf_10s = build_ltx23_i2v_workflow(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image_name=image_name,
        width=736,
        height=1280,
        length=241,
        steps=30,
        cfg=3.0,
        fps=25.0,
        filename_prefix="ltx23_i2v_beauty_dancing_10s"
    )

    with open("ltx23_i2v_beauty_dancing_5s.json", "w", encoding="utf-8") as f:
        json.dump(wf_5s, f, indent=2, ensure_ascii=False)
    print("已生成: ltx23_i2v_beauty_dancing_5s.json (121帧, 736x1280, 30步)")

    with open("ltx23_i2v_beauty_dancing_10s.json", "w", encoding="utf-8") as f:
        json.dump(wf_10s, f, indent=2, ensure_ascii=False)
    print("已生成: ltx23_i2v_beauty_dancing_10s.json (241帧, 736x1280, 30步)")


if __name__ == "__main__":
    main()
