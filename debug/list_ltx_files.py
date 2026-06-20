#!/usr/bin/env python3
"""列出 HuggingFace 上 LTX-2.3 的文件"""
from huggingface_hub import list_repo_files

repo = 'Lightricks/LTX-2.3'
print(f"=== {repo} 文件列表 ===")
files = list_repo_files(repo)
for f in sorted(files):
    if f.endswith('.safetensors') or f.endswith('.json') or f.endswith('.txt'):
        print(f)
