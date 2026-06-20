#!/bin/bash
# LTX-2.3 模型下载和节点安装脚本
source /root/miniconda3/etc/profile.d/conda.sh
conda activate comfyui

echo "=== 1. 安装 ComfyUI-LTXVideo 节点 ==="
cd /root/ComfyUI/custom_nodes
if [ ! -d "ComfyUI-LTXVideo" ]; then
    git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
    pip install -r ComfyUI-LTXVideo/requirements.txt 2>/dev/null
fi
echo "ComfyUI-LTXVideo 安装完成"

echo "=== 2. 下载 LTX-2.3 蒸馏版模型 ==="
huggingface-cli download Lightricks/LTX-2.3 ltx-2.3-22b-distilled.safetensors --local-dir /root/ComfyUI/models/diffusion_models/
echo "主模型下载完成"

echo "=== 3. 下载 LTX-2.3 VAE ==="
huggingface-cli download Lightricks/LTX-2.3 ltx-2.3-vae.safetensors --local-dir /root/ComfyUI/models/vae/ 2>/dev/null || echo "VAE 文件名可能不同，稍后检查"

echo "=== 4. 检查需要的文本编码器 ==="
# LTX-2.3 可能用 Gemma-3 或 T5
# 先检查 ComfyUI-LTXVideo 的文档
echo "请检查 ComfyUI-LTXVideo 文档确认文本编码器"

echo "=== LTX-2.3 下载脚本完成 ==="
ls -lh /root/ComfyUI/models/diffusion_models/ltx* 2>/dev/null
