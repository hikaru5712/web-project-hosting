import psutil
import os
import sys

def stop_webhosting_processes():
    """
    查找并停止所有与 WebHosting 相关的进程
    """
    print("正在查找 WebHosting 相关进程...")
    
    # 获取当前进程 ID，避免停止自己
    current_pid = os.getpid()
    
    # 存储要停止的进程
    processes_to_stop = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 检查进程是否是 Python 进程
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'pythonw.exe':
                # 检查命令行参数是否包含 WebHosting 相关内容
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmd_str = ' '.join(cmdline)
                    # 查找包含 manage.py runserver 或 service.py 的进程
                    if ('manage.py runserver' in cmd_str or 'service.py' in cmd_str) and proc.info['pid'] != current_pid:
                        processes_to_stop.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if not processes_to_stop:
        print("未找到 WebHosting 相关进程")
        return
    
    print(f"找到 {len(processes_to_stop)} 个 WebHosting 相关进程:")
    for proc in processes_to_stop:
        try:
            cmdline = ' '.join(proc.info.get('cmdline', []))
            print(f"  PID: {proc.info['pid']}, 命令: {cmdline[:100]}...")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    print("\n正在停止进程...")
    for proc in processes_to_stop:
        try:
            proc.terminate()
            print(f"  已停止进程 PID: {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"  无法停止进程 PID: {proc.info['pid']}")
    
    # 等待进程结束
    print("\n等待进程完全结束...")
    for proc in processes_to_stop:
        try:
            proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            pass
    
    print("\nWebHosting 服务已停止")

if __name__ == "__main__":
    stop_webhosting_processes()