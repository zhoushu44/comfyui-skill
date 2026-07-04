#!/usr/bin/env python3
"""Upload a file via SFTP and execute remotely"""
import sys
import os
import paramiko

def upload_and_run(host, port, user, password, local_path, remote_path, run_cmd=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=int(port), username=user, password=password, timeout=15)
        sftp = client.open_sftp()
        remote_dir = os.path.dirname(remote_path)
        if remote_dir:
            client.exec_command(f"mkdir -p '{remote_dir}'")
        sftp.put(local_path, remote_path)
        sftp.close()
        print(f"Uploaded: {local_path} -> {remote_path}")
        if run_cmd:
            print(f"\nRunning: {run_cmd}")
            stdin, stdout, stderr = client.exec_command(run_cmd, timeout=120)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            if out:
                print(out)
            if err:
                print(f"[stderr] {err}")
    finally:
        client.close()

if __name__ == "__main__":
    host = os.environ.get("SSH_HOST", "nc1kzw67mzphc18d.ssh.x-gpu.com")
    port = os.environ.get("SSH_PORT", "47424")
    user = os.environ.get("SSH_USER", "root")
    password = os.environ.get("SSH_PASS", "")
    # args: local_path remote_path [run_cmd]
    local = sys.argv[1]
    remote = sys.argv[2]
    run_cmd = sys.argv[3] if len(sys.argv) > 3 else None
    upload_and_run(host, port, user, password, local, remote, run_cmd)
