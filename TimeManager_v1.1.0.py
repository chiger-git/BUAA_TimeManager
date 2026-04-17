import sys
import os
import json
import urllib.request
import webbrowser
import threading
import math

from datetime import datetime, timedelta, date, time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QDialogButtonBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, 
    QLineEdit, QDateEdit, QTimeEdit, QLabel, QHeaderView, QComboBox,
    QMessageBox, QDialog, QListWidget, QAbstractItemView, QProgressBar, QSplashScreen,
    QGridLayout, QScrollArea, QColorDialog, QTreeWidget, QTreeWidgetItem, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate, QTime, QTimer, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QWheelEvent, QKeyEvent, QBrush, QIcon

CURRENT_VERSION = "1.1.0"
DATA_FILE = os.path.join(os.path.expanduser("~"), "buaa_todo_data_v2.json")

TIMETABLE = [
    "第1节\n08:00-08:45", "第2节\n08:50-09:35", "第3节\n09:50-10:35",
    "第4节\n10:40-11:25", "第5节\n11:30-12:15", "第6节\n14:00-14:45",
    "第7节\n14:50-15:35", "第8节\n15:50-16:35", "第9节\n16:40-17:25",
    "第10节\n19:00-19:45", "第11节\n19:50-20:35", "第12节\n20:40-21:25",
    "第13节\n21:30-22:15", "第14节\n22:20-23:05"
]

SEMESTER_START = date(2026, 2, 23)

DEFAULT_COURSE_SCHEDULE = [
    (0, 4, 5, "信号与系统", "F101", "付进", list(range(1, 17))),
    (0, 6, 9, "基础物理实验\n(磁光效应)", "学院路", "未知", [2]),
    (0, 6, 9, "基础物理实验\n(AFM虚拟仿真)", "学院路", "未知", [3]),
    (0, 6, 9, "基础物理实验\n(双棱镜干涉)", "学院路", "未知", [5]),
    (0, 6, 9, "基础物理实验\n(光电效应)", "学院路", "未知", [7]),
    (0, 6, 9, "基础物理实验\n(迈克尔逊干涉)", "学院路", "未知", [9]),
    (0, 6, 9, "基础物理实验\n(氢原子光谱)", "学院路", "未知", [11]),
    (0, 6, 9, "基础物理实验\n(阿贝成像)", "学院路", "未知", [12]),
    (0, 6, 9, "基础物理实验\n(巨磁阻效应)", "学院路", "未知", [16]),
    (1, 1, 2, "国家安全", "主南206", "孙泽斌", [6]),
    (1, 8, 9, "国家安全", "主南306", "孙泽斌", [11]),
    (1, 11, 12, "体育(4)[男排]", "体育馆副馆", "王晨", list(range(1, 17))),
    (2, 1, 2, "信号与系统", "F101", "付进", list(range(1, 17))),
    (2, 3, 4, "电磁场理论", "(三)102", "谢树果", [1, 2, 3] + list(range(5, 17))),
    (2, 6, 7, "形势与政策", "主203", "申文昊", [7]),
    (2, 11, 12, "心理健康", "主南408", "王慧琳", [7]),
    (3, 1, 2, "航空航天概论", "F228", "朱斯岩", list(range(1, 12))),
    (3, 3, 5, "马克思主义基本原理", "主北203", "李富君", list(range(1, 17))),
    (3, 6, 7, "电子电路", "主109", "刘荣科", list(range(1, 5))),
    (3, 6, 7, "电子电路", "主109", "陈立江", list(range(5, 17))),
    (3, 11, 14, "科研课堂", "空天电子信息实验中心", "杨彬", list(range(1, 9))),
    (4, 1, 2, "电子电路", "主109", "刘荣科", list(range(1, 5))),
    (4, 1, 2, "电子电路", "主109", "陈立江", list(range(5, 17))),
    (4, 6, 7, "电磁场理论", "(三)102", "谢树果", list(range(1, 17))),
    (4, 8, 9, "军事理论", "主M201", "黄敏杰", [1, 5, 9, 10, 12]),
    (5, 11, 14, "电子电路", "空天电子信息实验中心", "陈立江", [8, 10, 12, 14]),
    (6, 11, 13, "邂逅交响乐(2)", "晨兴剧场", "金刚, 张聪", [1, 2, 3, 4, 6, 7, 8, 9, 10])
]

DEFAULT_CATEGORIES = {
    "默认": "#FFFFFF",
    "学习": "#E6F7FF",
    "生活": "#FFF0F5",
    "紧急": "#FFE4E1"
}

class CategoryManagerDialog(QDialog):
    def __init__(self, categories, tasks=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理自定义分类")
        self.resize(320, 420)
        self.categories = categories # {"名称": "hex_color"}
        self.tasks = tasks if tasks is not None else []
        
        layout = QVBoxLayout(self)
        hint = QLabel("💡 可以在这里按需无限创建或重命名您偏好的课表/任务分类。\n注意：双击列表中的分类名即可重命名。删除分类会使原先隶属于该分类的任务回到无分类状态。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #555; padding-bottom: 10px;")
        layout.addWidget(hint)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.rename_category)
        self.refresh_list()
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("✚ 添加新分类")
        add_btn.clicked.connect(self.add_category)
        edit_btn = QPushButton("🎨 修改颜色")
        edit_btn.clicked.connect(self.edit_color)
        del_btn = QPushButton("✖ 删除某分类")
        del_btn.clicked.connect(self.del_category)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        
        close_btn = QPushButton("保存全部设置并完成")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def refresh_list(self):
        self.list_widget.clear()
        for cat, color in self.categories.items():
            item = QListWidgetItem(f"■ {cat}")
            item.setForeground(QColor("#000000"))
            self.list_widget.addItem(item)
            item.setBackground(QColor(color))
            
    def rename_category(self, item):
        from PyQt6.QtWidgets import QInputDialog
        old_cat = item.text().lstrip("■ ")
        new_cat, ok = QInputDialog.getText(self, '重命名分类', f'将【{old_cat}】重命名为（将同时更新属于该分类的所有任务）:', text=old_cat)
        new_cat = new_cat.strip()
        
        if ok and new_cat and new_cat != old_cat:
            if new_cat in self.categories:
                return QMessageBox.warning(self, "错误", "这个分类名称已经存在啦！")
                
            color = self.categories[old_cat]
            # 为了保存原有顺序
            new_dict = {}
            for k, v in self.categories.items():
                if k == old_cat:
                    new_dict[new_cat] = v
                else:
                    new_dict[k] = v
            self.categories.clear()
            self.categories.update(new_dict)
            
            # 同步更新它名下的所有任务，避免这些任务丢失分类
            default_cat = list(self.categories.keys())[0] if self.categories else ""
            for task in self.tasks:
                if task.get('category', default_cat) == old_cat:
                    task['category'] = new_cat
            self.refresh_list()
            
    def add_category(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, '添加分类', '请给您的新板块命名:')
        text = text.strip()
        if ok and text:
            if text in self.categories:
                return QMessageBox.warning(self, "错误", "该分类名称已经存在啦！")
            color = QColorDialog.getColor(Qt.GlobalColor.white, self, "选择该分类板块将会使用的背景颜色")
            if color.isValid():
                self.categories[text] = color.name()
                self.refresh_list()

    def edit_color(self):
        current = self.list_widget.currentItem()
        if not current: return
        cat = current.text().lstrip("■ ")
        old_color = self.categories.get(cat, "#FFFFFF")
        color = QColorDialog.getColor(QColor(old_color), self, f"给【{cat}】选择新的颜色")
        if color.isValid():
            self.categories[cat] = color.name()
            self.refresh_list()
            
    def del_category(self):
        from PyQt6.QtWidgets import QInputDialog
        cats = list(self.categories.keys())
        if not cats: return
        cat, ok = QInputDialog.getItem(self, "选择删除项", "请选择需要删除的分类：", cats, 0, False)
        if not ok or not cat: return
        
        default_cat = cats[0]
        affected_tasks = [t for t in self.tasks if t.get('category', default_cat) == cat]
        
        if affected_tasks:
            options = ["1. 将该分类及旗下所有任务全部删除", "2. 将任务转移到其他分类"]
            choice, ok_choice = QInputDialog.getItem(self, "处置所含任务", f"抱歉，在这之前我必须要问您一下：\n您将要删除的分类【{cat}】下现存 {len(affected_tasks)} 个任务。\n您希望如何处置它们？", options, 0, False)
            if not ok_choice: return
            
            if choice.startswith("1"):
                reply = QMessageBox.question(self, "极其高危提示", f"⚠️ 警告：这一步将会把分类【{cat}】和名下所有的任务彻底删除清空，无法恢复！\n再确认一遍：确定要删吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes: return
                self.tasks[:] = [t for t in self.tasks if t.get('category', default_cat) != cat]
            else:
                other_cats = [c for c in cats if c != cat]
                if not other_cats:
                    QMessageBox.warning(self, "尴尬了", "您并没有别的分类可供转移任务了！如果不保留，只能选择第一项全删或者先去建一个回收站分类。\n(将终止删除)")
                    return
                target_cat, ok_target = QInputDialog.getItem(self, "选择转移目的地", "请选择将任务安全转移到哪一个分类中存活：", other_cats, 0, False)
                if not ok_target or not target_cat: return
                for t in self.tasks:
                    if t.get('category', default_cat) == cat:
                        t['category'] = target_cat
        else:
            reply = QMessageBox.question(self, "删除空的分类", f"确定要彻底删除分类【{cat}】吗？因为它底下没有绑定任务，这很安全。", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes: return

        del self.categories[cat]
        self.refresh_list()

class TaskAssignmentDialog(QDialog):
    def __init__(self, tasks, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("在此时间段安排任务")
        self.resize(400, 500)
        self.selected_task = None
        self.tasks = tasks
        
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.lists = {}
        
        for cat in categories.keys():
            cat_list = QListWidget()
            cat_list.itemDoubleClicked.connect(self.assign_from_list)
            self.lists[cat] = cat_list
            self.tab_widget.addTab(cat_list, cat)
            
        has_pending = False
        default_cat = list(categories.keys())[0] if categories else ""
        for task in self.tasks:
            if task.get('status') == "Pending":
                cat = task.get('category', default_cat)
                if cat in self.lists:
                    self.lists[cat].addItem(task['name'])
                    has_pending = True
                elif default_cat in self.lists:
                    self.lists[default_cat].addItem(task['name'])
                    has_pending = True
                    
        if not has_pending and default_cat in self.lists:
            self.lists[default_cat].addItem("-- 没有待办任务 --")
            self.lists[default_cat].item(0).setFlags(Qt.ItemFlag.NoItemFlags)

        layout.addWidget(self.tab_widget)
        
        btn_layout = QHBoxLayout()
        assign_btn = QPushButton("安排此任务")
        assign_btn.clicked.connect(self.assign)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(assign_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def assign_from_list(self, item):
        if item.text() == "-- 没有待办任务 --": return
        self.selected_task = item.text()
        self.accept()

    def assign(self):
        current_list = self.tab_widget.currentWidget()
        selected_items = current_list.selectedItems()
        if not selected_items or selected_items[0].text() == "-- 没有待办任务 --":
            return QMessageBox.warning(self, "警告", "请先选择一个待办任务！")
        self.selected_task = selected_items[0].text()
        self.accept()

class UpdateCheckerThread(QThread):
    update_available = pyqtSignal(str, str, str) # version, log, url
    def run(self):
        try:
            url = "https://raw.githubusercontent.com/chiger-git/BUAA_TimeManager/main/update.json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                remote_version = data.get("version", "")
                if remote_version and remote_version != CURRENT_VERSION:
                    def v_to_tuple(v): return tuple(map(int, v.split('.')))
                    if v_to_tuple(remote_version) > v_to_tuple(CURRENT_VERSION):
                        self.update_available.emit(remote_version, data.get("update_log", ""), data.get("download_url", ""))
        except Exception as e:
            print("Update check failed:", e)

class BUAA_TimeManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BUAA Time Manager - ToDo & Schedule")
        self.resize(1050, 750)
        
        self.tasks = []
        self.schedule_assignments = {} 
        self.editing_task_name = None 
        self.categories = DEFAULT_CATEGORIES.copy()
        
        self.current_week = self.calculate_current_week()
        self.viewing_week = self.current_week
        self.preferences = {"font_family": "微软雅黑", "font_size": 12}
        
        self.load_data()
        self.init_ui()
        
        app_font = QFont(self.preferences.get("font_family", "微软雅黑"), self.preferences.get("font_size", 12))
        self.setFont(app_font)
        
        self.update_thread = UpdateCheckerThread()
        self.update_thread.update_available.connect(self.show_update_dialog)
        self.update_thread.start()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_task_list)
        self.timer.start(60000)

    def show_update_dialog(self, version, log, url):
        msg = QMessageBox(self)
        msg.setWindowTitle("发现新版本")
        msg.setText(f"检测到新版本 v{version}，当您版本当前处于 v{CURRENT_VERSION}。\n不更新也可继续使用。是否选择前往网页更新？\n\n【更新提要】\n{log}")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("前往更新")
        msg.button(QMessageBox.StandardButton.No).setText("暂不升级")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            webbrowser.open(url)

    def calculate_current_week(self):
        today = date.today()
        delta = today - SEMESTER_START
        week = delta.days // 7
        return max(1, week)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0: self.zoom_in()
            elif delta < 0: self.zoom_out()
            return True
        return super().eventFilter(obj, event)

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.tab_todo = QWidget()
        self.tab_schedule = QWidget()
        self.tab_courses = QWidget()
        self.tab_settings = QWidget()

        self.tabs.addTab(self.tab_todo, "📥 任务列表")
        self.tabs.addTab(self.tab_schedule, "📅 周视图课表")
        self.tabs.addTab(self.tab_courses, "📚 自定义课程管理")
        self.tabs.addTab(self.tab_settings, "⚙ 偏好设置")

        self.init_settings_tab()
        self.init_todo_tab()
        self.init_schedule_tab()
        self.init_course_tab()
        
        self.apply_global_styles()

    def apply_global_styles(self):
        # Add bold horizontal headers to make it look nicer
        self.setStyleSheet("""
            QHeaderView::section {
                font-weight: bold;
                background-color: #e0e0e0;
                color: #000000;
                padding: 4px;
            }
        """)

    def init_settings_tab(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        hint = QLabel("💡 在这里您可以全局自定义界面的显示字体。\n在进行缩放时，推荐按住 Ctrl + 鼠标滚轮进行无缝平滑浏览。\n您可以随时按下（Ctrl+0）恢复默认的 12 字号。")
        hint.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(hint)
        
        form = QFormLayout()
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["微软雅黑", "宋体", "楷体", "Arial"])
        current_font = self.preferences.get("font_family", "微软雅黑")
        self.font_combo.setCurrentText(current_font)
        
        # Adding combo buttons container
        size_layout = QHBoxLayout()
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([str(i) for i in range(8, 37)])
        current_size = str(self.preferences.get("font_size", 12))
        self.font_size_combo.setCurrentText(current_size)
        size_layout.addWidget(self.font_size_combo)
        
        reset_zoom_btn = QPushButton("↺ 恢复12字号(Ctrl+0)")
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        size_layout.addWidget(reset_zoom_btn)
        
        form.addRow("A  选择界面字体:", self.font_combo)
        form.addRow("T  调整界面字号:", size_layout)
        
        apply_btn = QPushButton("保存全部文字并应用修改")
        apply_btn.clicked.connect(self.apply_font_settings)
        
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addSpacing(20)
        
    def reset_zoom(self):
        self.font_size_combo.setCurrentText("12")
        self.apply_font_settings(silent=True)
        
    def apply_font_settings(self, silent=False):
        font_family = self.font_combo.currentText()
        font_size = int(self.font_size_combo.currentText())
        
        self.preferences["font_family"] = font_family
        self.preferences["font_size"] = font_size
        
        app_font = QFont(font_family, font_size)
        self.setFont(app_font)
        
        # *闪烁修复点*：我们在修改字号时，不要去无脑 resizeRowsToContents() 强制干扰 Schedule，它本来就靠垂直拉伸（Stretch）完美填满
        for t in getattr(self, 'task_tables', []):
            t.resizeRowsToContents()
            
        # course_table 仍可自适应
        self.course_table.resizeRowsToContents()
        
        self.save_data()
        if not silent:
            QMessageBox.information(self, "成功", "您当前的设置已经被记录并全局生效！")
            
    def manage_categories(self):
        dlg = CategoryManagerDialog(self.categories, self.tasks, self)
        dlg.exec()
        default_cat = list(self.categories.keys())[0] if self.categories else ""
        for task in self.tasks:
            if task.get('category', default_cat) not in self.categories:
                task['category'] = default_cat
        self.category_combo.clear()
        self.category_combo.addItems(list(self.categories.keys()))
        self.save_data()
        self.refresh_task_list()

    def init_todo_tab(self):
        layout = QVBoxLayout(self.tab_todo)
        
        input_layout = QHBoxLayout()
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("新任务...")
        input_layout.addWidget(self.task_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.categories.keys()))
        input_layout.addWidget(self.category_combo)
        
        manage_cat_btn = QPushButton("⚙管理分类")
        manage_cat_btn.clicked.connect(self.manage_categories)
        input_layout.addWidget(manage_cat_btn)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        input_layout.addWidget(self.date_input)
        
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime(23, 59)) 
        input_layout.addWidget(self.time_input)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pending", "Completed"])
        input_layout.addWidget(self.status_combo)
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_task)
        input_layout.addWidget(add_btn)
        
        save_btn = QPushButton("保存修改")
        save_btn.clicked.connect(self.save_edit)
        input_layout.addWidget(save_btn)
        
        layout.addLayout(input_layout)
        
        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)
        self.task_grid_widget = QWidget()
        self.task_grid = QGridLayout(self.task_grid_widget)
        self.task_scroll.setWidget(self.task_grid_widget)
        layout.addWidget(self.task_scroll)
        
        ops_layout = QHBoxLayout()
        del_btn = QPushButton("删除以上选中打标的任务")
        del_btn.clicked.connect(self.delete_task)
        ops_layout.addWidget(del_btn)
        
        mark_btn = QPushButton("一键切换完成/未完成状态")
        mark_btn.clicked.connect(self.toggle_task_status)
        ops_layout.addWidget(mark_btn)
        
        layout.addLayout(ops_layout)
        self.task_tables = []
        self.refresh_task_list()

    def get_selected_tasks(self):
        selected_names = []
        for t in self.task_tables:
            rows = list(set([item.row() for item in t.selectedItems()]))
            for r in rows:
                selected_names.append(t.item(r, 0).text())
        return selected_names

    def delete_task(self):
        names = self.get_selected_tasks()
        if not names: return
        self.tasks = [t for t in self.tasks if t['name'] not in names]
        keys_to_del = [k for k, v in self.schedule_assignments.items() if v in names]
        for k in keys_to_del:
            del self.schedule_assignments[k]
        self.save_data()
        self.refresh_task_list()
        self.refresh_schedule_view()

    def toggle_task_status(self):
        names = self.get_selected_tasks()
        for task in self.tasks:
            if task['name'] in names:
                task['status'] = "Completed" if task['status'] == "Pending" else "Pending"
        self.save_data()
        self.refresh_task_list()
        self.refresh_schedule_view()

    def refresh_task_list(self):
        while self.task_grid.count():
            item = self.task_grid.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
            
        self.task_tables.clear()
        
        cats = list(self.categories.keys())
        n = len(cats)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols) if cols > 0 else 1
        
        for i, cat in enumerate(cats):
            r, c = i // cols, i % cols
            
            group_box = QWidget()
            g_layout = QVBoxLayout(group_box)
            g_layout.setContentsMargins(4, 4, 4, 4)
            
            lbl = QLabel(f" ■ 任务组别：{cat}")
            lbl.setStyleSheet("font-weight: bold; background-color: transparent;")
            g_layout.addWidget(lbl)
            
            table = QTableWidget()
            table.viewport().installEventFilter(self)
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["待办事项名称", "倒计时限时", "状态"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setWordWrap(True)
            table.cellDoubleClicked.connect(self.on_task_double_clicked_delegate(table))
            
            bg_color = self.categories.get(cat, "#FFFFFF")
            table.setStyleSheet(f"QTableWidget {{ background-color: {bg_color}; border-radius: 4px; }}")
            
            g_layout.addWidget(table)
            self.task_grid.addWidget(group_box, r, c)
            self.task_tables.append(table)

            default_cat = cats[0] if cats else ""
            cat_tasks = [t for t in self.tasks if t.get('category', default_cat) == cat]
            cat_tasks.sort(key=lambda x: (x['status'] == 'Completed', x['deadline']))

            table.setRowCount(len(cat_tasks))
            for row, task in enumerate(cat_tasks):
                item_name = QTableWidgetItem(task['name'])
                item_name.setData(Qt.ItemDataRole.UserRole, task['deadline'])
                
                friendly_str = self.get_friendly_time_str(task['deadline'])
                item_friendly = QTableWidgetItem(friendly_str)
                item_status = QTableWidgetItem(task['status'])
                
                task_bg = None
                if task['status'] == "Completed":
                    task_bg = QColor(200, 255, 200)
                elif "逾期" in friendly_str:
                    task_bg = QColor(255, 200, 200)
                    
                for col, item in enumerate([item_name, item_friendly, item_status]):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setForeground(QBrush(QColor(0,0,0)))
                    if task_bg:
                        item.setBackground(task_bg)
                    table.setItem(row, col, item)
            table.resizeRowsToContents()

    def on_task_double_clicked_delegate(self, table_ref):
        def handler(row, column):
            task_name = table_ref.item(row, 0).text()
            raw_dl = table_ref.item(row, 0).data(Qt.ItemDataRole.UserRole)
            status = table_ref.item(row, 2).text()
            
            default_cat = list(self.categories.keys())[0] if self.categories else ""
            cat = default_cat
            for t in self.tasks:
                if t['name'] == task_name:
                    cat = t.get('category', default_cat)
                    break
            
            self.task_input.setText(task_name)
            self.status_combo.setCurrentText(status)
            self.category_combo.setCurrentText(cat)
            
            try:
                dt = datetime.strptime(raw_dl, "%Y-%m-%d %H:%M")
                self.date_input.setDate(QDate(dt.year, dt.month, dt.day))
                self.time_input.setTime(QTime(dt.hour, dt.minute))
            except: pass
            self.editing_task_name = task_name
        return handler

    def init_schedule_tab(self):
        layout = QVBoxLayout(self.tab_schedule)
        
        week_nav_layout = QHBoxLayout()
        prev_btn = QPushButton("◀ 上一周")
        prev_btn.clicked.connect(self.prev_week)
        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.week_label.setFont(font)
        next_btn = QPushButton("下一周 ▶")
        next_btn.clicked.connect(self.next_week)
        curr_btn = QPushButton("回到本周")
        curr_btn.clicked.connect(self.go_current_week)
        
        week_nav_layout.addWidget(prev_btn)
        week_nav_layout.addWidget(self.week_label)
        week_nav_layout.addWidget(next_btn)
        week_nav_layout.addWidget(curr_btn)
        layout.addLayout(week_nav_layout)
        
        self.schedule_table = QTableWidget()
        self.schedule_table.viewport().installEventFilter(self)
        self.schedule_table.setRowCount(14)
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setHorizontalHeaderLabels(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        self.schedule_table.setVerticalHeaderLabels(TIMETABLE)
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # 移除 Stretch，允许随字号撑开并出现滚动条，从而解决“周视图直接动弹不了”的问题
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # 修改左侧纵向表头 padding 和微小字号，避免文字顶住上下边界线截断
        self.schedule_table.setStyleSheet(self.schedule_table.styleSheet() + """
            QHeaderView::section:vertical {
                padding: 1px;
                font-size: 11px;
                color: #333;
            }
        """)
        
        self.schedule_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.schedule_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.schedule_table.setWordWrap(True)
        
        self.schedule_table.cellClicked.connect(self.on_schedule_clicked)
        self.schedule_table.cellDoubleClicked.connect(self.on_schedule_double_clicked)
        layout.addWidget(self.schedule_table)
        
        clear_btn = QPushButton("清空本周所有已安排的任务 (不影响课程)")
        clear_btn.clicked.connect(self.clear_schedule_tasks)
        layout.addWidget(clear_btn)
        
        self.reload_and_refresh()

    def init_course_tab(self):
        layout = QVBoxLayout(self.tab_courses)
        hint = QLabel("💡 在此管理您的所有固定课程。添加/删除后周课表将自动同步。")
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)
        
        self.course_table = QTableWidget()
        self.course_table.viewport().installEventFilter(self)
        self.course_table.setColumnCount(7)
        self.course_table.setHorizontalHeaderLabels(["星期", "开始节次", "结束节次", "课程名称", "教室", "教师", "上课周次"])
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.course_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.course_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.course_table)
        
        ops_layout = QHBoxLayout()
        add_btn = QPushButton("✚ 添加新课程")
        add_btn.clicked.connect(self.add_new_course)
        ops_layout.addWidget(add_btn)
        del_btn = QPushButton("✖ 删除选中课程")
        del_btn.clicked.connect(self.delete_selected_course)
        ops_layout.addWidget(del_btn)
        reset_btn = QPushButton("↺ 恢复系统默认课表")
        reset_btn.clicked.connect(self.reset_to_default_courses)
        ops_layout.addWidget(reset_btn)
        layout.addLayout(ops_layout)
        self.refresh_course_list()

    def refresh_course_list(self):
        self.course_table.setRowCount(0)
        for i, course in enumerate(self.courses):
            self.course_table.insertRow(i)
            day, start, end, name, room, teacher, weeks = course
            self.course_table.setItem(i, 0, QTableWidgetItem(f"星期 {day + 1}"))
            self.course_table.setItem(i, 1, QTableWidgetItem(str(start)))
            self.course_table.setItem(i, 2, QTableWidgetItem(str(end)))
            self.course_table.setItem(i, 3, QTableWidgetItem(name))
            self.course_table.setItem(i, 4, QTableWidgetItem(room))
            self.course_table.setItem(i, 5, QTableWidgetItem(teacher))
            weeks_str = f"共 {len(weeks)} 周"
            if weeks:
                weeks_str = f"{min(weeks)}-{max(weeks)}周" if len(weeks) > 1 else f"第{weeks[0]}周"
            self.course_table.setItem(i, 6, QTableWidgetItem(weeks_str))

    def add_new_course(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("添加新课程")
        dialog.resize(350, 280)
        form = QFormLayout(dialog)
        name_input = QLineEdit(); form.addRow("课程名称:", name_input)
        room_input = QLineEdit(); form.addRow("上课教室:", room_input)
        teacher_input = QLineEdit(); form.addRow("授课教师:", teacher_input)
        day_combo = QComboBox(); day_combo.addItems(["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]); form.addRow("星期:", day_combo)
        start_spin = QSpinBox(); start_spin.setRange(1, 14); form.addRow("开始节次:", start_spin)
        end_spin = QSpinBox(); end_spin.setRange(1, 14); form.addRow("结束节次:", end_spin)
        weeks_input = QLineEdit(); weeks_input.setPlaceholderText("填入格式如: 1-16"); form.addRow("上课周次:", weeks_input)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        form.addRow(btns)
        if dialog.exec():
            name = name_input.text().strip() or "新建课程"
            room = room_input.text().strip() or "未知"
            teacher = teacher_input.text().strip() or "无"
            day = day_combo.currentIndex()
            start = start_spin.value(); end = end_spin.value()
            if start > end: start, end = end, start
            weeks = set()
            try:
                for part in weeks_input.text().replace("，", ",").split(","):
                    if "-" in part: s, e = map(int, part.split("-")); weeks.update(range(s, e + 1))
                    elif part.isdigit(): weeks.add(int(part))
            except: pass
            if not weeks: weeks = set(range(1, 17))
            self.courses.append((day, start, end, name, room, teacher, sorted(list(weeks))))
            self.save_data()
            self.refresh_course_list()
            self.reload_and_refresh()

    def delete_selected_course(self):
        row = self.course_table.currentRow()
        if row >= 0:
            if QMessageBox.question(self, "删除确认", "真的要删除此课程吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.courses.pop(row)
                self.save_data()
                self.refresh_course_list()
                self.reload_and_refresh()
                
    def reset_to_default_courses(self):
        if QMessageBox.warning(self, "恢复默认", "确定要清空自定义并恢复为默认的北航课表吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.courses = list(DEFAULT_COURSE_SCHEDULE)
            self.save_data()
            self.refresh_course_list()
            self.reload_and_refresh()

    def prev_week(self):
        if self.viewing_week > 1:
            self.viewing_week -= 1
            self.reload_and_refresh()

    def next_week(self):
        if self.viewing_week < 20: 
            self.viewing_week += 1
            self.reload_and_refresh()

    def reload_and_refresh(self):
        self.load_data()
        self.refresh_schedule_view()

    def go_current_week(self):
        self.viewing_week = self.current_week
        self.reload_and_refresh()

    def get_friendly_time_str(self, dt_str):
        try: target_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except: return dt_str 
            
        now = datetime.now()
        target_date = target_dt.date()
        today = now.date()
        time_str = target_dt.strftime("%H:%M")
        delta = (target_date - today).days
        
        if delta < 0: return f"逾期 ({target_dt.strftime('%m-%d %H:%M')})"
        elif delta == 0: return f"今日逾期 ({time_str})" if target_dt < now else f"今天 {time_str}"
        elif delta == 1: return f"明天 {time_str}"
        elif delta == 2: return f"后天 {time_str}"
        elif 2 < delta < 7:
            wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            return f"本{wd[target_date.weekday()]} {time_str}" if target_date.weekday() > today.weekday() and (today + timedelta(days=7 - today.weekday())) > target_date else f"下{wd[target_date.weekday()]} {time_str}"
        else: return target_dt.strftime("%Y-%m-%d %H:%M")

    def add_task(self):
        name = self.task_input.text().strip()
        date_val = self.date_input.date().toString("yyyy-MM-dd")
        time_val = self.time_input.time().toString("HH:mm")
        status = self.status_combo.currentText()
        cat = self.category_combo.currentText()
        
        if not name: return QMessageBox.warning(self, "错误", "任务名称不能为空！")
        if any(t['name'] == name for t in self.tasks): return QMessageBox.warning(self, "警告", "已存在同名任务！")
            
        self.tasks.append({
            "name": name,
            "deadline": f"{date_val} {time_val}",
            "status": status,
            "category": cat
        })
        self.task_input.clear()
        self.editing_task_name = None 
        self.save_data()
        self.refresh_task_list()

    def save_edit(self):
        if not self.editing_task_name: return QMessageBox.warning(self, "提示", "请双击任务行。")
        new_name = self.task_input.text().strip()
        date_val = self.date_input.date().toString("yyyy-MM-dd")
        time_val = self.time_input.time().toString("HH:mm")
        new_status = self.status_combo.currentText()
        new_cat = self.category_combo.currentText()
        if not new_name: return
        
        if new_name != self.editing_task_name and any(t['name'] == new_name for t in self.tasks):
            return QMessageBox.warning(self, "警告", "名称冲突。")
        
        for task in self.tasks:
            if task['name'] == self.editing_task_name:
                task['name'] = new_name
                task['deadline'] = f"{date_val} {time_val}"
                task['status'] = new_status
                task['category'] = new_cat
                break
                
        if new_name != self.editing_task_name:
            for k, t_name in list(self.schedule_assignments.items()):
                if t_name == self.editing_task_name:
                    self.schedule_assignments[k] = new_name
                    
        self.task_input.clear()
        self.editing_task_name = None
        self.save_data()
        self.refresh_task_list()
        self.refresh_schedule_view()

    def refresh_schedule_view(self):
        if self.viewing_week == self.current_week:
            self.week_label.setText(f"◆ 第 {self.viewing_week} 周[本周] ◆")
        else:
            self.week_label.setText(f"第 {self.viewing_week} 周")
            
        self.schedule_table.clearContents()
        
        for course in self.courses:
            day, start, end, name, room, teacher, weeks = course
            if self.viewing_week in weeks:
                for period in range(start - 1, end):
                    item = QTableWidgetItem(f"[上课]\n{name}\n{room}\n{teacher}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QColor(220, 220, 220)) 
                    item.setForeground(QColor(80, 80, 80))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    item.setData(Qt.ItemDataRole.UserRole, "locked")
                    item.setData(Qt.ItemDataRole.UserRole + 1, f"课程名称：{name}\n上课周次：第 {weeks[0]}-{weeks[-1]} 周\n教室：{room}\n教师：{teacher}")
                    self.schedule_table.setItem(period, day, item)
                
        for key, task_name in self.schedule_assignments.items():
            if not isinstance(key, tuple) or len(key) != 3: continue
            week, day, period = int(key[0]), int(key[1]), int(key[2])
            if week != self.viewing_week: continue
                
            curr = self.schedule_table.item(period, day)
            if curr is None or curr.data(Qt.ItemDataRole.UserRole) != "locked":
                default_cat = list(self.categories.keys())[0] if self.categories else ""
                cat, status = default_cat, "Pending"
                for t in self.tasks:
                    if t['name'] == task_name:
                        status = t['status']
                        cat = t.get('category', default_cat)
                        break
                
                item = QTableWidgetItem(f"[{cat}]\n{task_name}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor(0,0,0)))
                
                base_color = self.categories.get(cat, "#B0E0E6")
                if status == "Completed":
                    item.setBackground(QColor(200, 255, 200))
                else:
                    try: item.setBackground(QColor(base_color))
                    except: item.setBackground(QColor(176, 224, 230))
                
                item.setData(Qt.ItemDataRole.UserRole, "task")
                self.schedule_table.setItem(period, day, item)
                
    def on_schedule_clicked(self, row, column):
        item = self.schedule_table.item(row, column)
        if item and item.data(Qt.ItemDataRole.UserRole) == "locked":
            QMessageBox.information(self, "课程详细信息", item.data(Qt.ItemDataRole.UserRole + 1))
            
    def on_schedule_double_clicked(self, row, column):
        item = self.schedule_table.item(row, column)
        if item and item.data(Qt.ItemDataRole.UserRole) == "locked": return
            
        if item and item.data(Qt.ItemDataRole.UserRole) == "task":
            if QMessageBox.question(self, "取消任务安排", "确定要将该任务移出当前的时间段吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                key = (self.viewing_week, column, row)
                str_key = str(key)
                if key in self.schedule_assignments: del self.schedule_assignments[key]
                elif str_key in self.schedule_assignments: del self.schedule_assignments[str_key]
                else:
                    for k in list(self.schedule_assignments.keys()):
                        if str(k) == str_key: del self.schedule_assignments[k]
                self.save_data()
                self.reload_and_refresh()
            return
            
        dialog = TaskAssignmentDialog(self.tasks, self.categories, self)
        if dialog.exec():
            self.schedule_assignments[(int(self.viewing_week), int(column), int(row))] = dialog.selected_task 
            self.save_data()
            self.reload_and_refresh()

    def clear_schedule_tasks(self):
        if QMessageBox.warning(self, "清空确认", f"确定清空 第{self.viewing_week}周 课表上所有已安排的任务吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            for k in list(self.schedule_assignments.keys()):
                try:
                    w = int(k.strip('()').split(',')[0]) if isinstance(k, str) else k[0]
                    if w == self.viewing_week: del self.schedule_assignments[k]
                except: pass
            self.save_data()
            self.reload_and_refresh()

    def load_data(self):
        self.courses = list(DEFAULT_COURSE_SCHEDULE)
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.categories = data.get("categories", DEFAULT_CATEGORIES.copy())
                    if data.get("courses") is not None: self.courses = data.get("courses")
                    self.preferences = data.get("preferences", {"font_family": "微软雅黑", "font_size": 12})
                    self.schedule_assignments = {}
                    for k_str, val in data.get("schedule", {}).items():
                        parts = k_str.strip('()').split(',')
                        if len(parts) == 2: self.schedule_assignments[(self.current_week, int(parts[0]), int(parts[1]))] = val
                        elif len(parts) == 3: self.schedule_assignments[(int(parts[0]), int(parts[1]), int(parts[2]))] = val
            except Exception as e: print(f"Error loading: {e}")

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding='utf-8') as f:
                json.dump({
                    "tasks": self.tasks,
                    "categories": self.categories,
                    "schedule": {str(k): v for k, v in self.schedule_assignments.items()},
                    "courses": self.courses,
                    "preferences": self.preferences
                }, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Error saving data: {e}")

    def wheelEvent(self, event: QWheelEvent):
        if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0: self.zoom_in()
            elif delta < 0: self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Equal or event.key() == Qt.Key.Key_Plus:
                self.zoom_in()
                event.accept()
            elif event.key() == Qt.Key.Key_Minus:
                self.zoom_out()
                event.accept()
            elif event.key() == Qt.Key.Key_0:
                self.reset_zoom()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def zoom_in(self):
        size = self.preferences.get("font_size", 12)
        if size < 36:
            self.font_size_combo.setCurrentText(str(size + 1))
            self.apply_font_settings(silent=True)

    def zoom_out(self):
        size = self.preferences.get("font_size", 12)
        if size > 8:
            self.font_size_combo.setCurrentText(str(size - 1))
            self.apply_font_settings(silent=True)

class StartupLoader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    def run(self):
        import time
        for i in range(1, 101):
            time.sleep(0.012)
            self.progress.emit(i)
        self.finished.emit()

class ModernSplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QColor(245, 250, 252))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 500, 300, 20, 20)
        
        painter.setBrush(QColor(176, 224, 230))
        painter.drawRoundedRect(0, 0, 500, 180, 20, 20)
        
        painter.setPen(QColor(0, 0, 0))
        font = QFont("Arial", 26, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, 0, 0, -120), Qt.AlignmentFlag.AlignCenter, "BUAA Time Manager")
        
        font.setPointSize(12)
        font.setWeight(QFont.Weight.Normal)
        painter.drawText(pixmap.rect().adjusted(0, 80, 0, -120), Qt.AlignmentFlag.AlignCenter, "Spring 2026 Edition v" + CURRENT_VERSION)
        
        painter.end()
        super().__init__(pixmap)
        
        layout = QVBoxLayout(self)
        layout.addStretch()
        
        self.progressBar = QProgressBar()
        self.progressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E0E0E0;
                height: 12px;
                border-radius: 6px;
                margin-left: 40px;
                margin-right: 40px;
            }
            QProgressBar::chunk { background-color: #4682B4; border-radius: 6px; }
        """)
        self.progressBar.setTextVisible(False)
        
        self.statusLabel = QLabel("Initializing Environment...")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.setStyleSheet("color: #666666; font-family: Arial; font-size: 12px; margin-bottom: 30px;")
        
        layout.addWidget(self.progressBar)
        layout.addWidget(self.statusLabel)
        
    def updateProgress(self, value):
        self.progressBar.setValue(value)
        if value < 30: self.statusLabel.setText("正在加载依赖项库...")
        elif value < 70: self.statusLabel.setText("正在配置全新任务分类视图...")
        elif value < 95: self.statusLabel.setText("正在读取您的本地任务与偏好设置...")
        else: self.statusLabel.setText("启动就绪，准备加载界面...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    splash = ModernSplashScreen()
    splash.show()
    
    window = None
    def start_main_window():
        global window
        window = BUAA_TimeManager()
        window.show()
        splash.finish(window)
        
    loader = StartupLoader()
    loader.progress.connect(splash.updateProgress)
    loader.finished.connect(start_main_window)
    loader.start()
    
    sys.exit(app.exec())
