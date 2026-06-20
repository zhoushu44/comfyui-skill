#!/bin/bash
# 下载 LTX-2.3 需要的额外模型
source /root/miniconda3/etc/profile.d/conda.sh
conda activate comfyui

echo "=== 1. 移动主模型到 checkpoints 目录 ==="
mv /root/ComfyUI/models/diffusion_models/ltx-2.3-22b-distilled.safetensors /root/ComfyUI/models/checkpoints/ 2>/dev/null
ls -lh /root/ComfyUI/models/checkpoints/ltx* 2>/dev/null

echo "=== 2. 下载 Gemma-3 文本编码器 ==="
huggingface-cli download Comfy-Org/itx-2 gemma_3_12B_it_fp4_mixed.safetensors --local-dir /root/ComfyUI/models/text_encoders/

echo "=== 3. 下载蒸馏 LoRA ==="
huggingface-cli download Lightricks/LTX-2.3 ltx-2.3-22b-distilled-lora-384-1.1.safetensors --local-dir /root/ComfyUI/models/loras/ltxv/

echo "=== 4. 下载空间放大器（可选）==="
huggingface-cli download Lightricks/LTX-2.3 ltx-2.3-spatial-upscaler-x2-1.1.safetensors --local-dir /root/ComfyUI/models/latent_upscale_models/

echo "=== LTX-2.3 模型下载完成 ==="
ls -lh /root/ComfyUI/models/checkpoints/ltx* 2>/dev/null
ls -lh /root/ComfyUI/models/text_encoders/gemma* 2>/dev/null
ls -lh /root/ComfyUI/models/loras/ltxv/ 2>/dev/null
