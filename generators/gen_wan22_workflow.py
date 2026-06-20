#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基于 Wan 2.2 i2v 模板生成 5s 和 10s 工作流"""
import json
import copy

# 读取模板
with open(r'C:\Users\zs\.trae-cn\skills\comfyui-workflow\templates\wan22-img2vid.json', 'r', encoding='utf-8') as f:
    template = json.load(f)

# 服务器上的模型文件名
HIGH_NOISE_MODEL = "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
LOW_NOISE_MODEL = "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
TEXT_ENCODER = "umt5_xxl_fp16.safetensors"
VAE = "wan_2.1_vae.safetensors"
CLIP_VISION = "clip_vision_h.safetensors"  # 需要确认服务器上是否有

# 提示词
PROMPT = "a beautiful young woman in red dress dancing gracefully, elegant movements, spinning around, fluid motion, high quality, cinematic"
NEG_PROMPT = "blurry, distorted, low quality, static, jittery, deformed, bad anatomy, watermark"

# 分辨率（竖屏，能被 16 整除）
WIDTH = 736
HEIGHT = 1280

# 帧数配置（Wan 2.2 @ 16fps）
# 5s = 81帧, 10s = 161帧
DURATIONS = {
    "5s": {"length": 81, "fps": 16},
    "10s": {"length": 161, "fps": 16}
}

def modify_workflow(template, duration_name, length, fps):
    """修改工作流参数"""
    wf = copy.deepcopy(template)
    
    for node in wf["nodes"]:
        # UNETLoader - 修改模型文件名
        if node["type"] == "UNETLoader":
            wv = node["widgets_values"]
            # 服务器上有 high_noise 和 low_noise 两个模型
            # 模板中可能有一个或两个 UNETLoader
            if "high" in str(wv[0]).lower() or wv[0] == "":
                wv[0] = HIGH_NOISE_MODEL
            elif "low" in str(wv[0]).lower():
                wv[0] = LOW_NOISE_MODEL
            else:
                # 默认用 high_noise
                wv[0] = HIGH_NOISE_MODEL
            wv[1] = "fp8_e4m3fn"  # weight dtype
        
        # CLIPLoader - 文本编码器
        elif node["type"] == "CLIPLoader":
            node["widgets_values"][0] = TEXT_ENCODER
        
        # VAELoader
        elif node["type"] == "VAELoader":
            node["widgets_values"][0] = VAE
        
        # CLIPVisionLoader
        elif node["type"] == "CLIPVisionLoader":
            node["widgets_values"][0] = CLIP_VISION
        
        # CLIPTextEncode - 正向提示词
        elif node["type"] == "CLIPTextEncode" and node.get("title", "") == "Positive Prompt":
            node["widgets_values"][0] = PROMPT
        
        # CLIPTextEncode - 负面提示词
        elif node["type"] == "CLIPTextEncode" and node.get("title", "") == "Negative Prompt":
            node["widgets_values"][0] = NEG_PROMPT
        
        # WanImageToVideo - 修改分辨率和帧数
        elif node["type"] in ("WanImageToVideo", "WanImageToVideoGPU", "WanVaceToVideo"):
            wv = node["widgets_values"]
            # widgets_values 顺序通常是: width, height, length, batch_size, ...
            for i, v in enumerate(wv):
                if i == 0 and isinstance(v, int):
                    wv[i] = WIDTH
                elif i == 1 and isinstance(v, int):
                    wv[i] = HEIGHT
                elif i == 2 and isinstance(v, int):
                    wv[i] = length
        
        # KSampler - 修改采样参数
        elif node["type"] == "KSampler":
            wv = node["widgets_values"]
            # widgets_values: seed, control_after_generate, steps, cfg, sampler_name, scheduler, denoise
            if len(wv) >= 7:
                wv[2] = 30  # steps
                wv[3] = 3.5  # cfg
                wv[4] = "euler"  # sampler
                wv[5] = "simple"  # scheduler
        
        # SaveAnimatedWEBP - 修改 FPS 和文件名
        elif node["type"] == "SaveAnimatedWEBP":
            wv = node["widgets_values"]
            # widgets_values: filename_prefix, fps, lossless, quality, method
            if len(wv) >= 2:
                wv[0] = f"wan22_i2v_beauty_dancing_{duration_name}"
                wv[1] = fps  # fps
    
    # 更新 models 数组
    wf["models"] = [
        {
            "name": HIGH_NOISE_MODEL,
            "url": f"https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/{HIGH_NOISE_MODEL}",
            "directory": "diffusion_models"
        },
        {
            "name": LOW_NOISE_MODEL,
            "url": f"https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/{LOW_NOISE_MODEL}",
            "directory": "diffusion_models"
        },
        {
            "name": TEXT_ENCODER,
            "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp16.safetensors",
            "directory": "text_encoders"
        },
        {
            "name": VAE,
            "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",
            "directory": "vae"
        },
        {
            "name": CLIP_VISION,
            "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors",
            "directory": "clip_vision"
        }
    ]
    
    return wf

# 生成两个版本
for duration_name, config in DURATIONS.items():
    wf = modify_workflow(template, duration_name, config["length"], config["fps"])
    filename = f"wan22_i2v_beauty_dancing_{duration_name}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print(f"生成: {filename} ({config['length']}帧, {config['fps']}fps, {WIDTH}x{HEIGHT})")

print("\n工作流生成完成！")
