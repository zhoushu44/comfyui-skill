#!/usr/bin/env python3
"""查找正确的 Gemma-3 文本编码器仓库"""
from huggingface_hub import list_repo_files

# 尝试几个可能的仓库
repos = [
    'Comfy-Org/ltx-2',
    'Comfy-Org/LTX-2',
    'comfyanonymous/gemma_3_12B_it_fp4_mixed',
    'Lightricks/gemma-3-12b-it',
]

for repo in repos:
    try:
        files = list_repo_files(repo)
        gemma_files = [f for f in files if 'gemma' in f.lower() and f.endswith('.safetensors')]
        if gemma_files:
            print(f"\n=== {repo} ===")
            for f in gemma_files:
                print(f"  {f}")
    except Exception as e:
        print(f"\n{repo}: {type(e).__name__}")
