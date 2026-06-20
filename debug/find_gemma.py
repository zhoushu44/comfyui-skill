#!/usr/bin/env python3
"""下载 LTX-2.3 需要的 Gemma-3 文本编码器"""
from huggingface_hub import list_repo_files, hf_hub_download
import shutil, os

# 检查 Lightricks/LTX-2.3 仓库中的所有文件
repo = 'Lightricks/LTX-2.3'
print(f"=== {repo} 所有文件 ===")
files = list_repo_files(repo)
for f in sorted(files):
    print(f"  {f}")

# 检查是否有 gemma 文件
gemma_files = [f for f in files if 'gemma' in f.lower()]
print(f"\n=== Gemma 文件 ===")
for f in gemma_files:
    print(f"  {f}")
