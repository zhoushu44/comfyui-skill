#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSH 命令执行工具（通过 paramiko）"""
import sys
import os
import paramiko

def ssh_exec(host, port, user, password, commands, max_retries=3):
    """执行 SSH 命令并输出结果（带重试）"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connected = False
    for attempt in range(max_retries):
        try:
            client.connect(host, port=int(port), username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
            connected = True
            break
        except Exception as e:
            print(f"[连接重试 {attempt+1}/{max_retries}] {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(5)
    if not connected:
        print("SSH 连接失败，请检查服务器状态")
        return
    try:
        for cmd in commands:
            print(f"\n{'='*60}")
            print(f"执行: {cmd}")
            print('='*60)
            stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')
            if out:
                print(out)
            if err:
                print(f"[stderr] {err}")
    finally:
        client.close()

if __name__ == '__main__':
    host = os.environ.get('SSH_HOST', 'nc1kzw67mzphc18d.ssh.x-gpu.com')
    port = os.environ.get('SSH_PORT', '47424')
    user = os.environ.get('SSH_USER', 'root')
    password = os.environ.get('SSH_PASS', '')
    commands = sys.argv[1:] if len(sys.argv) > 1 else ['hostname']
    ssh_exec(host, port, user, password, commands)
