import os
import subprocess
import shutil

print("====================================================")
print(" BUAA Time Manager 高阶安装程序封装器 (Two-Stage Build)")
print("====================================================")

# 确保安装了 pyinstaller
try:
    import PyInstaller
except ImportError:
    print("未检测到 PyInstaller，正在安装...")
    subprocess.check_call(["pip", "install", "pyinstaller"])

icon_path = r"D:\2026_Spring\TimeManageTools\TimeManager.ico"
script_path = r"D:\2026_Spring\TimeManageTools\TimeManager_v1.1.0.py"
setup_script_path = r"D:\2026_Spring\TimeManageTools\setup_wizard.py"
app_exe_path = r"D:\2026_Spring\TimeManageTools\dist\BUAA日程管理.exe"

# 第一阶段：编译核心主程序
print("\n【阶段 1/2】开始编译您的核心业务逻辑为无环境单体应用...")
cmd_app = [
    "pyinstaller",
    "--noconfirm",
    "--windowed",  # 无黑框
    "--onefile",   # 单文件
    "--name", "BUAA日程管理",
    "--icon", icon_path,
    script_path
]
subprocess.check_call(cmd_app)

print("\n【阶段 2/2】核心程序就绪！现在将它嵌入我们亲自编写的可视化安装向导中...")
# --add-data "文件;存放相对路径" 是PyInstaller的内置文件绑定语法
cmd_setup = [
    "pyinstaller",
    "--noconfirm",
    "--windowed",
    "--onefile",
    "--name", "BUAA日程管理_一键安装向导",
    "--icon", icon_path,
    "--add-data", f"{app_exe_path};.",
    setup_script_path
]
subprocess.check_call(cmd_setup)


print("\n✅ 所有封装任务全部成功！")
print(r"最终您要发给您朋友的文件：D:\2026_Spring\TimeManageTools\dist\BUAA日程管理_一键安装向导.exe")
print("您的朋友拿到这个向导后，会像安装QQ一样经历 路径选择 -> 静默解压释放 -> 桌面快捷方式部署等全套商业体验。")
