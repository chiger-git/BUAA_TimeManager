import sys
import os
import shutil
import subprocess
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton, QHBoxLayout, QCheckBox, 
                             QProgressBar, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class InstallerThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, target_dir, make_shortcut):
        super().__init__()
        self.target_dir = target_dir
        self.make_shortcut = make_shortcut

    def run(self):
        try:
            self.progress.emit(10)
            self.log.emit("准备提取核心文件...")
            
            # PyInstaller打包后，附加文件会释放在 sys._MEIPASS 临时目录
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            src_exe = os.path.join(base_path, "BUAA日程管理.exe")
            if not os.path.exists(src_exe):
                self.log.emit(f"错误：找不到安装包内的核心文件！({src_exe})")
                self.finished.emit(False)
                return

            # 创建安装目录
            os.makedirs(self.target_dir, exist_ok=True)
            dest_exe = os.path.join(self.target_dir, "BUAA日程管理.exe")

            self.progress.emit(40)
            self.log.emit("正在复制应用文件到目标路径...")
            shutil.copy2(src_exe, dest_exe)

            self.progress.emit(80)
            if self.make_shortcut:
                self.log.emit("正在配置桌面快捷方式...")
                vbs_path = os.path.join(os.environ["TEMP"], "create_lnk.vbs")
                vbs_code = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sDesk = oWS.SpecialFolders("Desktop")
Set oLink = oWS.CreateShortcut(sDesk & "\\BUAA日程管理.lnk")
oLink.TargetPath = "{dest_exe}"
oLink.WorkingDirectory = "{self.target_dir}"
oLink.WindowStyle = 1
oLink.Save'''
                with open(vbs_path, "w", encoding="utf-16") as f:
                    f.write(vbs_code)
                
                # 静默执行 vbs
                subprocess.run(["wscript.exe", vbs_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

            self.progress.emit(100)
            self.log.emit("所有操作完成！")
            self.finished.emit(True)

        except Exception as e:
            self.log.emit(f"发生错误: {str(e)}")
            self.finished.emit(False)

class SetupWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BUAA 日程管理 - 安装向导")
        self.resize(480, 260)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 欢迎标题
        title = QLabel("欢迎安装 BUAA 日程管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4682B4; margin-bottom: 5px;")
        layout.addWidget(title)
        
        subtitle = QLabel("本向导将引导您完成应用环境的部署。")
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # 安装路径选择
        layout.addWidget(QLabel("请选择为您解压安装的路径:"))
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        # 默认装在 LocalAppData 防 C盘 Program Files 的管理员权限弹窗拦截
        default_path = os.path.join(os.environ['LOCALAPPDATA'], "BUAATimeManager")
        self.path_input.setText(default_path)
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("浏览位置...")
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # 快捷方式复选框
        self.shortcut_cb = QCheckBox("在桌面上创建应用快捷方式")
        self.shortcut_cb.setChecked(True)
        self.shortcut_cb.setStyleSheet("margin-top: 15px; margin-bottom: 10px;")
        layout.addWidget(self.shortcut_cb)

        # 进度与状态
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {border: none; background-color: #E0E0E0; height: 10px; border-radius: 5px;}
            QProgressBar::chunk {background-color: #4682B4; border-radius: 5px;}
        """)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 底部安装按钮
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.install_btn = QPushButton("立即安装")
        self.install_btn.setMinimumWidth(120)
        self.install_btn.setMinimumHeight(35)
        self.install_btn.setStyleSheet("background-color: #4682B4; color: white; font-weight: bold; border-radius: 4px;")
        self.install_btn.clicked.connect(self.start_install)
        btn_layout.addWidget(self.install_btn)
        layout.addLayout(btn_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择安装目录", self.path_input.text())
        if folder:
            self.path_input.setText(os.path.normpath(folder))

    def start_install(self):
        self.install_btn.setEnabled(False)
        self.path_input.setEnabled(False)
        self.shortcut_cb.setEnabled(False)
        self.install_btn.setText("正在安装中...")

        target_dir = self.path_input.text().strip()
        make_shortcut = self.shortcut_cb.isChecked()

        self.thread = InstallerThread(target_dir, make_shortcut)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.log.connect(self.status_label.setText)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, success):
        if success:
            QMessageBox.information(self, "安装完成", "BUAA 日程管理 已经成功安装到您的电脑！\\n请前往您选择的目录或桌面快捷方式体验。")
            sys.exit(0)
        else:
            self.install_btn.setEnabled(True)
            self.install_btn.setText("重试")
            self.path_input.setEnabled(True)
            self.shortcut_cb.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())