import os
import sys
import subprocess
import paramiko

HOST = '192.168.51.67'
USER = 'admin'
PASSWORD = 'jxsdboy22'
LOCAL = '/Users/jacking/tools/demo/ai-model-compare.tar.gz'
REMOTE = '/home/admin/ai-model-compare.tar.gz'

PROJECT_ROOT = '/Users/jacking/tools/demo'

def create_tarball():
    """Create a tar.gz package in LOCAL with standard exclusions."""
    tar_cmd = [
        'tar', '-czf', LOCAL,
        "--exclude=.git",
        "--exclude=__pycache__",
        "--exclude=*.pyc",
        "--exclude=.DS_Store",
        "--exclude=.venv",
        "--exclude=venv",
        "--exclude=data/*.sqlite3",

        "--exclude=*.log",
        "--exclude=nohup.out",
        "--exclude=*.tar.gz",
        'app', 'static', 'templates', 'config', 'tools',
        'requirements.txt', 'README.md', 'DEPLOYMENT.md', 'QUICK_START.md', 'TROUBLESHOOTING.md',
        'nginx.conf', 'supervisor.conf', 'deploy.sh', 'upload.sh', 'models-export.json'
    ]
    result = subprocess.run(tar_cmd, cwd=PROJECT_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"打包失败: {result.stderr.strip()}")

try:
    # 先本地打包
    create_tarball()
    if not os.path.exists(LOCAL):
        raise FileNotFoundError(f'本地文件不存在: {LOCAL}')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=10)

    sftp = client.open_sftp()

    # 确保远程目录存在（若无权限则忽略）
    try:
        sftp.chdir('/home/admin')
    except IOError:
        sftp.mkdir('/home/admin')
        sftp.chdir('/home/admin')

    sftp.put(LOCAL, REMOTE)
    sftp.close()
    client.close()
    print('UPLOAD_OK')
except Exception as e:
    print(f'ERROR: {e.__class__.__name__}: {e}')
    sys.exit(1)


