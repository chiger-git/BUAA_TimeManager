from PIL import Image, ImageDraw
import os
import subprocess
import sys

def create_icon():
    # 创建一个透明背景的图像
    img = Image.new('RGBA', (256, 256), color=(255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    
    # 淡蓝色底色，与我们的界面主题呼应
    bg_color = (176, 224, 230) 
    d.rounded_rectangle([(16, 16), (240, 240)], radius=50, fill=bg_color)
    
    # 画一个简约的白色时钟
    d.ellipse([(58, 58), (198, 198)], outline="white", width=15)
    
    # 时针和分针
    d.line([(128, 128), (128, 85)], fill="white", width=15, joint="curve")
    d.line([(128, 128), (165, 128)], fill="white", width=15, joint="curve")

    icon_path = r"D:\2026_Spring\TimeManageTools\TimeManager.ico"
    img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    return icon_path

def create_shortcut(icon_path):
    vbs_path = r"D:\2026_Spring\TimeManageTools\create_lnk.vbs"
    launcher_bat_path = r"D:\2026_Spring\TimeManageTools\launch_TimeManager.bat"
    launcher_vbs_path = r"D:\2026_Spring\TimeManageTools\launch_TimeManager.vbs"
    script_path = r"D:\2026_Spring\TimeManageTools\TimeManager.py"
    
    # 1. 创建批处理文件激活环境并运行程序
    bat_code = f"""@echo off
call conda activate MyAnaconda
start pythonw "{script_path}"
"""
    with open(launcher_bat_path, "w", encoding="utf-8") as f:
        f.write(bat_code)

    # 2. 创建 VBScript 隐藏黑框执行上一级的 bat 文件
    launcher_code = f"""Set oShell = CreateObject("WScript.Shell")
oShell.Run "{launcher_bat_path}", 0, False
"""
    with open(launcher_vbs_path, "w", encoding="utf-8") as f:
        f.write(launcher_code)
    
    # 3. VBScript 创建桌面快捷方式，将目标指向由于上述产生的隐藏执行器
    vbs_code = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sDesk = oWS.SpecialFolders("Desktop")
Set oLink = oWS.CreateShortcut(sDesk & "\\BUAA日程管理.lnk")
oLink.TargetPath = "wscript.exe"
oLink.Arguments = \"""{launcher_vbs_path}\"""
oLink.IconLocation = "{icon_path}"
oLink.WorkingDirectory = "D:\\2026_Spring\\TimeManageTools"
oLink.WindowStyle = 1
oLink.Save
"""
    # utf-16 编码来安全处理中文路径
    with open(vbs_path, "w", encoding="utf-16") as f:
        f.write(vbs_code)
        
    subprocess.run(["cscript", "//nologo", vbs_path], shell=True)
    
    # 清理临时 vbs 文件
    if os.path.exists(vbs_path):
        os.remove(vbs_path)

if __name__ == "__main__":
    try:
        icon_path = create_icon()
        create_shortcut(icon_path)
        print("Success")
    except Exception as e:
        print("Error:", e)
