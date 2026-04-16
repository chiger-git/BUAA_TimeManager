import sys
import os
import json
import urllib.request
import webbrowser
import threading

from datetime import datetime, timedelta, date, time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QDialogButtonBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, 
    QLineEdit, QDateEdit, QTimeEdit, QLabel, QHeaderView, QComboBox,
    QMessageBox, QDialog, QListWidget, QAbstractItemView, QProgressBar, QSplashScreen
)
from PyQt6.QtCore import Qt, QDate, QTime, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter

CURRENT_VERSION = "1.0.1"
DATA_FILE = os.path.join(os.path.expanduser("~"), "buaa_todo_data_v2.json")

# 定义北航的上课时间表
TIMETABLE = [
    "第1节\n08:00-08:45", "第2节\n08:50-09:35", "第3节\n09:50-10:35",
    "第4节\n10:40-11:25", "第5节\n11:30-12:15", "第6节\n14:00-14:45",
    "第7节\n14:50-15:35", "第8节\n15:50-16:35", "第9节\n16:40-17:25",
    "第10节\n19:00-19:45", "第11节\n19:50-20:35", "第12节\n20:40-21:25",
    "第13节\n21:30-22:15", "第14节\n22:20-23:05"
]

# 学期基准开学日期（假设2026年春季学期 2月23日 开学，星期一）
SEMESTER_START = date(2026, 2, 23)

# 课表定义：(星期 0-6, 开始节次 1-14, 结束节次 1-14, 课程名称, 教室, 教师, 参与周次)
DEFAULT_COURSE_SCHEDULE = [
    # 星期一
    (0, 4, 5, "信号与系统", "F101", "付进", list(range(1, 17))),
    (0, 6, 9, "基础物理实验\n(磁光效应)", "学院路", "未知", [2]),
    (0, 6, 9, "基础物理实验\n(AFM虚拟仿真)", "学院路", "未知", [3]),
    (0, 6, 9, "基础物理实验\n(双棱镜干涉)", "学院路", "未知", [5]),
    (0, 6, 9, "基础物理实验\n(光电效应)", "学院路", "未知", [7]),
    (0, 6, 9, "基础物理实验\n(迈克尔逊干涉)", "学院路", "未知", [9]),
    (0, 6, 9, "基础物理实验\n(氢原子光谱)", "学院路", "未知", [11]),
    (0, 6, 9, "基础物理实验\n(阿贝成像)", "学院路", "未知", [12]),
    (0, 6, 9, "基础物理实验\n(巨磁阻效应)", "学院路", "未知", [16]),
    # 星期二
    (1, 1, 2, "国家安全", "主南206", "孙泽斌", [6]),
    (1, 8, 9, "国家安全", "主南306", "孙泽斌", [11]),
    (1, 11, 12, "体育(4)[男排]", "体育馆副馆", "王晨", list(range(1, 17))),
    # 星期三
    (2, 1, 2, "信号与系统", "F101", "付进", list(range(1, 17))),
    (2, 3, 4, "电磁场理论", "(三)102", "谢树果", [1, 2, 3] + list(range(5, 17))),
    (2, 6, 7, "形势与政策", "主203", "申文昊", [7]),
    (2, 11, 12, "心理健康", "主南408", "王慧琳", [7]),
    # 星期四
    (3, 1, 2, "航空航天概论", "F228", "朱斯岩", list(range(1, 12))),
    (3, 3, 5, "马克思主义基本原理", "主北203", "李富君", list(range(1, 17))),
    (3, 6, 7, "电子电路", "主109", "刘荣科", list(range(1, 5))),
    (3, 6, 7, "电子电路", "主109", "陈立江", list(range(5, 17))),
    (3, 11, 14, "科研课堂", "空天电子信息实验中心", "杨彬", list(range(1, 9))),
    # 星期五
    (4, 1, 2, "电子电路", "主109", "刘荣科", list(range(1, 5))),
    (4, 1, 2, "电子电路", "主109", "陈立江", list(range(5, 17))),
    (4, 6, 7, "电磁场理论", "(三)102", "谢树果", list(range(1, 17))),
    (4, 8, 9, "军事理论", "主M201", "黄敏杰", [1, 5, 9, 10, 12]),
    # 星期六
    (5, 11, 14, "电子电路", "空天电子信息实验中心", "陈立江", [8, 10, 12, 14]),
    # 星期日
    (6, 11, 13, "邂逅交响乐(2)", "晨兴剧场", "金刚, 张聪", [1, 2, 3, 4, 6, 7, 8, 9, 10])
]


class TaskAssignmentDialog(QDialog):
    """用于在课表中选择并分配任务的任务选择框"""
    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self.setWindowTitle("在此时间段安排任务")
        self.resize(300, 400)
        self.selected_task = None
        
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.tasks = tasks
        
        for task in self.tasks:
            if task['status'] == "Pending":
                self.list_widget.addItem(task['name'])
                
        if self.list_widget.count() == 0:
            self.list_widget.addItem("-- 没有待办任务 --")
            self.list_widget.item(0).setFlags(Qt.ItemFlag.NoItemFlags)

        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        assign_btn = QPushButton("安排此任务")
        assign_btn.clicked.connect(self.assign)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(assign_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def assign(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items or selected_items[0].text() == "-- 没有待办任务 --":
            QMessageBox.warning(self, "警告", "请先选择一个待办任务！")
            return
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
                    # Simple version string compare, assumes format x.y.z
                    def v_to_tuple(v):
                        return tuple(map(int, v.split('.')))
                    if v_to_tuple(remote_version) > v_to_tuple(CURRENT_VERSION):
                        self.update_available.emit(remote_version, data.get("update_log", ""), data.get("download_url", ""))
        except Exception as e:
            print("Update check failed:", e)

class BUAA_TimeManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BUAA Time Manager - ToDo & Schedule")
        self.resize(1000, 700)
        
        self.tasks = []
        self.schedule_assignments = {} # format: {(week, day, period): task_name}
        self.editing_task_name = None # 记录当前正在编辑的任务名称
        
        self.current_week = self.calculate_current_week()
        self.viewing_week = self.current_week
        self.preferences = {"font_family": "微软雅黑", "font_size": 12}
        
        self.load_data()
        self.init_ui()
        
        # Apply initial font
        app_font = QFont(self.preferences["font_family"], self.preferences["font_size"])
        QApplication.instance().setFont(app_font)
        
        # Check for updates
        self.update_thread = UpdateCheckerThread()
        self.update_thread.update_available.connect(self.show_update_dialog)
        self.update_thread.start()
        
        # 定时器：每分钟刷新一次相对时间显示
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_task_list)
        self.timer.start(60000)

    
    def show_update_dialog(self, version, log, url):
        msg = QMessageBox(self)
        msg.setWindowTitle("发现新版本")
        msg.setText(f"检测到新版本 v{version}，当前版本 v{CURRENT_VERSION}。是否前往更新？\n\n更新内容：\n{log}")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("前往更新")
        msg.button(QMessageBox.StandardButton.No).setText("跳过此版本")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            webbrowser.open(url)

    def calculate_current_week(self):
        today = date.today()
        delta = today - SEMESTER_START
        week = delta.days // 7
        return max(1, week)  # 至少是第一周

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.tab_todo = QWidget()
        self.tab_schedule = QWidget()
        self.tab_courses = QWidget()  # 新增：课程管理
        self.tab_settings = QWidget()

        self.tabs.addTab(self.tab_todo, "📥 任务列表")
        self.tabs.addTab(self.tab_schedule, "📅 周视图课表")
        self.tabs.addTab(self.tab_courses, "📚 自定义课程管理")
        self.tabs.addTab(self.tab_settings, "⚙ 偏好设置")

        self.init_todo_tab()
        self.init_schedule_tab()
        self.init_course_tab()
        self.init_settings_tab()

    def init_settings_tab(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        hint = QLabel("💡 在这里您可以自定义界面的显示字体。修改后会立即生效。")
        hint.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(hint)
        
        form = QFormLayout()
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["微软雅黑", "宋体", "楷体"])
        current_font = self.preferences.get("font_family", "微软雅黑")
        self.font_combo.setCurrentText(current_font)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["10", "11", "12", "14", "16", "18"])
        current_size = str(self.preferences.get("font_size", 12))
        self.font_size_combo.setCurrentText(current_size)
        
        form.addRow("选择界面字体:", self.font_combo)
        form.addRow("选择界面字号(默认12):", self.font_size_combo)
        
        apply_btn = QPushButton("保存并应用设置")
        apply_btn.clicked.connect(self.apply_font_settings)
        
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        
        # 增加对表格的全局列宽自动折行设置以防止截断
        self.task_table.setWordWrap(True)
        self.schedule_table.setWordWrap(True)
        self.course_table.setWordWrap(True)
        
    def apply_font_settings(self):
        font_family = self.font_combo.currentText()
        font_size = int(self.font_size_combo.currentText())
        
        self.preferences["font_family"] = font_family
        self.preferences["font_size"] = font_size
        
        app_font = QFont(font_family, font_size)
        QApplication.instance().setFont(app_font)
        
        # 为了防止大字体被表格截断，每次修改字体都让表格调整行高
        for table in [self.task_table, self.schedule_table, self.course_table]:
            table.resizeRowsToContents()
            
        self.save_data()
        QMessageBox.information(self, "成功", "设置已保存并全局生效。")

    def init_todo_tab(self):
        layout = QVBoxLayout(self.tab_todo)
        
        # 输入区
        input_layout = QHBoxLayout()
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("在此输入新任务...")
        input_layout.addWidget(self.task_input)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        input_layout.addWidget(self.date_input)
        
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime(23, 59)) # 默认今晚23:59
        input_layout.addWidget(self.time_input)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pending", "Completed"])
        input_layout.addWidget(self.status_combo)
        
        add_btn = QPushButton("添加任务")
        add_btn.clicked.connect(self.add_task)
        input_layout.addWidget(add_btn)
        
        save_btn = QPushButton("保存修改")
        save_btn.clicked.connect(self.save_edit)
        input_layout.addWidget(save_btn)
        
        layout.addLayout(input_layout)
        
        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["任务名称", "原始截止日期", "截止时间 (智能换算)", "状态"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        self.task_table.cellDoubleClicked.connect(self.on_task_double_clicked)
        
        layout.addWidget(self.task_table)
        
        # 操作区
        ops_layout = QHBoxLayout()
        del_btn = QPushButton("删除选中任务")
        del_btn.clicked.connect(self.delete_task)
        ops_layout.addWidget(del_btn)
        
        mark_btn = QPushButton("切换完成状态")
        mark_btn.clicked.connect(self.toggle_task_status)
        ops_layout.addWidget(mark_btn)
        
        layout.addLayout(ops_layout)
        self.refresh_task_list()

    def init_schedule_tab(self):
        layout = QVBoxLayout(self.tab_schedule)
        
        # 周次导航栏
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
        self.schedule_table.setRowCount(14)
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setHorizontalHeaderLabels(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        self.schedule_table.setVerticalHeaderLabels(TIMETABLE)
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.schedule_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 绑定单击和双击事件
        self.schedule_table.cellClicked.connect(self.on_schedule_clicked)
        self.schedule_table.cellDoubleClicked.connect(self.on_schedule_double_clicked)
        
        layout.addWidget(self.schedule_table)
        
        clear_btn = QPushButton("清空本周所有已安排的任务 (不影响课程)")
        clear_btn.clicked.connect(self.clear_schedule_tasks)
        layout.addWidget(clear_btn)
        
        self.reload_and_refresh()

    def init_course_tab(self):
        layout = QVBoxLayout(self.tab_courses)
        
        # 说明
        hint = QLabel("💡 在此管理您的所有固定课程。添加/删除后周课表将自动同步。")
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)
        
        # 课程表格
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(7)
        self.course_table.setHorizontalHeaderLabels(["星期 (1-7)", "开始节次", "结束节次", "课程名称", "教室", "教师", "上课周次"])
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.course_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.course_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.course_table)
        
        # 操作区
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
            # 内部星期 0代表周一，展示时+1
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
        
        name_input = QLineEdit()
        form.addRow("课程名称:", name_input)
        
        room_input = QLineEdit()
        form.addRow("上课教室:", room_input)
        
        teacher_input = QLineEdit()
        form.addRow("授课教师:", teacher_input)
        
        day_combo = QComboBox()
        day_combo.addItems(["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"])
        form.addRow("星期:", day_combo)
        
        start_spin = QSpinBox(); start_spin.setRange(1, 14)
        end_spin = QSpinBox(); end_spin.setRange(1, 14)
        form.addRow("开始节次:", start_spin)
        form.addRow("结束节次:", end_spin)
        
        weeks_input = QLineEdit()
        weeks_input.setPlaceholderText("填入格式如: 1-16")
        form.addRow("上课周次:", weeks_input)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        form.addRow(btns)
        
        if dialog.exec():
            name = name_input.text().strip() or "新建课程"
            room = room_input.text().strip() or "未知"
            teacher = teacher_input.text().strip() or "无"
            day = day_combo.currentIndex()
            start = start_spin.value()
            end = end_spin.value()
            if start > end: start, end = end, start
            
            # 简单解析周次 "1-16"
            weeks_str = weeks_input.text().strip()
            weeks = set()
            try:
                for part in weeks_str.replace("，", ",").split(","):
                    if "-" in part:
                        s, e = map(int, part.split("-"))
                        weeks.update(range(s, e + 1))
                    elif part.isdigit():
                        weeks.add(int(part))
            except Exception:
                pass
            if not weeks: weeks = set(range(1, 17))
            
            new_course = (day, start, end, name, room, teacher, sorted(list(weeks)))
            self.courses.append(new_course)
            
            self.save_data()
            self.refresh_course_list()
            self.reload_and_refresh()

    def delete_selected_course(self):
        row = self.course_table.currentRow()
        if row >= 0:
            reply = QMessageBox.question(self, "删除确认", "真的要删除此课程的所有安排吗？", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.courses.pop(row)
                self.save_data()
                self.refresh_course_list()
                self.reload_and_refresh()
                
    def reset_to_default_courses(self):
        reply = QMessageBox.warning(self, "恢复默认", "确定要清空自定义并恢复为默认的北航课表吗？", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.courses = list(DEFAULT_COURSE_SCHEDULE)
            self.save_data()
            self.refresh_course_list()
            self.reload_and_refresh()

    def prev_week(self):
        if self.viewing_week > 1:
            self.viewing_week -= 1
            self.reload_and_refresh()

    def next_week(self):
        if self.viewing_week < 20: # 假设最多20周
            self.viewing_week += 1
            self.reload_and_refresh()

    def reload_and_refresh(self):
        """重新加载最新数据以防止缓存格式污染"""
        self.load_data()
        self.refresh_schedule_view()

    def go_current_week(self):
        self.viewing_week = self.current_week
        self.reload_and_refresh()

    def get_friendly_time_str(self, dt_str):
        try:
            target_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return dt_str # 回退处理
            
        now = datetime.now()
        target_date = target_dt.date()
        today = now.date()
        
        time_str = target_dt.strftime("%H:%M")
        delta_days = (target_date - today).days
        
        if delta_days < 0:
            return f"逾期 ({target_dt.strftime('%m-%d %H:%M')})"
        elif delta_days == 0:
            # 判断今天是否已经过了该时间
            if target_dt < now:
                return f"今日已逾期 ({time_str})"
            return f"今天 {time_str}"
        elif delta_days == 1:
            return f"明天 {time_str}"
        elif delta_days == 2:
            return f"后天 {time_str}"
        elif 2 < delta_days < 7:
            # 判断是否在下周
            target_weekday = target_date.weekday()
            today_weekday = today.weekday()
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            
            if target_weekday > today_weekday and (today + timedelta(days=7 - today_weekday)) > target_date:
                return f"本{weekdays[target_weekday]} {time_str}"
            else:
                return f"下{weekdays[target_weekday]} {time_str}"
        else:
            return target_dt.strftime("%Y-%m-%d %H:%M")

    def refresh_task_list(self):
        self.task_table.setRowCount(0)
        # 排序：按未完成优先，时间紧优先
        sorted_tasks = sorted(self.tasks, key=lambda x: (x['status'] == 'Completed', x['deadline']))
        
        for task in sorted_tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            
            item_name = QTableWidgetItem(task['name'])
            item_raw_dl = QTableWidgetItem(task['deadline'])
            
            friendly_str = self.get_friendly_time_str(task['deadline'])
            item_friendly_dl = QTableWidgetItem(friendly_str)
            
            item_status = QTableWidgetItem(task['status'])
            
            if task['status'] == "Completed":
                bg_color = QColor(200, 255, 200) # 完成标绿
            elif "逾期" in friendly_str:
                bg_color = QColor(255, 200, 200) # 逾期标红
            else:
                bg_color = None
            
            for i, item in enumerate([item_name, item_raw_dl, item_friendly_dl, item_status]):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # 列表文字居中对齐
                if bg_color:
                    item.setBackground(bg_color)
                    item.setForeground(QColor(0, 0, 0)) # 强制黑色字体保证清晰度
                self.task_table.setItem(row, i, item)

    def add_task(self):
        name = self.task_input.text().strip()
        date_val = self.date_input.date().toString("yyyy-MM-dd")
        time_val = self.time_input.time().toString("HH:mm")
        status = self.status_combo.currentText()
        
        if not name:
            QMessageBox.warning(self, "错误", "任务名称不能为空！")
            return
            
        # 检查是否重复
        for task in self.tasks:
            if task['name'] == name:
                QMessageBox.warning(self, "警告", "已存在同名任务！请使用不同的名称或修改现有任务。")
                return
            
        deadline = f"{date_val} {time_val}"
        
        self.tasks.append({
            "name": name,
            "deadline": deadline,
            "status": status
        })
        
        self.task_input.clear()
        self.editing_task_name = None # 重置编辑状态
        self.save_data()
        self.refresh_task_list()

    def on_task_double_clicked(self, row, column):
        # 双击任务列表行以编辑
        task_name = self.task_table.item(row, 0).text()
        raw_deadline = self.task_table.item(row, 1).text()
        status = self.task_table.item(row, 3).text()
        
        self.task_input.setText(task_name)
        self.status_combo.setCurrentText(status)
        
        try:
            dt = datetime.strptime(raw_deadline, "%Y-%m-%d %H:%M")
            self.date_input.setDate(QDate(dt.year, dt.month, dt.day))
            self.time_input.setTime(QTime(dt.hour, dt.minute))
        except ValueError:
            pass
            
        self.editing_task_name = task_name

    def save_edit(self):
        if not self.editing_task_name:
            QMessageBox.warning(self, "提示", "请先在下方的列表中双击需要修改的任务行，然后再点击保存修改。")
            return
            
        new_name = self.task_input.text().strip()
        date_val = self.date_input.date().toString("yyyy-MM-dd")
        time_val = self.time_input.time().toString("HH:mm")
        new_status = self.status_combo.currentText()
        
        if not new_name:
            QMessageBox.warning(self, "错误", "任务名称不能为空！")
            return
            
        new_deadline = f"{date_val} {time_val}"
        
        # 如果名称改变了，检查新名称是否与其他任务冲突
        if new_name != self.editing_task_name:
            for task in self.tasks:
                if task['name'] == new_name:
                    QMessageBox.warning(self, "警告", "修改后的任务名称与现有任务冲突，请使用不同名称。")
                    return
        
        # 更新任务列表
        for task in self.tasks:
            if task['name'] == self.editing_task_name:
                task['name'] = new_name
                task['deadline'] = new_deadline
                task['status'] = new_status
                break
                
        # 同步更新课表中对于该任务的安排
        if new_name != self.editing_task_name:
            for key, t_name in self.schedule_assignments.items():
                if t_name == self.editing_task_name:
                    self.schedule_assignments[key] = new_name
                    
        self.task_input.clear()
        self.editing_task_name = None
        self.save_data()
        self.refresh_task_list()
        self.refresh_schedule_view()

    def delete_task(self):
        selected_rows = list(set([item.row() for item in self.task_table.selectedItems()]))
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先点击选中的一行或多行任务，然后再点击删除。")
            return
        
        task_names = [self.task_table.item(row, 0).text() for row in selected_rows]
        
        # 删除任务并从课表关联中清理
        self.tasks = [t for t in self.tasks if t['name'] not in task_names]
        keys_to_del = [k for k, v in self.schedule_assignments.items() if v in task_names]
        for k in keys_to_del:
            del self.schedule_assignments[k]
            
        self.save_data()
        self.refresh_task_list()
        self.refresh_schedule_view()

    def toggle_task_status(self):
        selected_rows = list(set([item.row() for item in self.task_table.selectedItems()]))
        if not selected_rows:
            return
        
        task_names = [self.task_table.item(row, 0).text() for row in selected_rows]
        
        for task in self.tasks:
            if task['name'] in task_names:
                task['status'] = "Completed" if task['status'] == "Pending" else "Pending"
                
        self.save_data()
        self.refresh_task_list()

    def refresh_schedule_view(self):
        # 刷新本周标签
        if self.viewing_week == self.current_week:
            self.week_label.setText(f"◆ 第 {self.viewing_week} 周[本周] ◆")
        else:
            self.week_label.setText(f"第 {self.viewing_week} 周")
            
        self.schedule_table.clearContents()
        
        # 填充本周的课程（锁定并标灰）
        for course in self.courses:
            day, start, end, name, room, teacher, weeks = course
            # 只有本周有该课才会显示
            if self.viewing_week in weeks:
                for period in range(start - 1, end):
                    item = QTableWidgetItem(f"[上课]\n{name}\n{room}\n{teacher}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QColor(220, 220, 220)) # 灰色背景代表不可用
                    item.setForeground(QColor(100, 100, 100))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    item.setData(Qt.ItemDataRole.UserRole, "locked")
                    
                    # 存储课程详细信息留作点击显示
                    details = f"课程名称：{name}\n上课周次：第 {weeks[0]}-{weeks[-1]} 周\n教室：{room}\n教师：{teacher}"
                    item.setData(Qt.ItemDataRole.UserRole + 1, details)
                    
                    self.schedule_table.setItem(period, day, item)
                
        # 填充本周已安排的任务
        for key, task_name in self.schedule_assignments.items():
            # 兼容处理，防止键的格式由于历史原因有误
            if not isinstance(key, tuple) or len(key) != 3:
                continue
                
            week, day, period = int(key[0]), int(key[1]), int(key[2])
            if week != self.viewing_week:
                continue
                
            current_item = self.schedule_table.item(period, day)
            if current_item is None or current_item.data(Qt.ItemDataRole.UserRole) != "locked":
                # 检查任务是否已完成
                task_status = "Pending"
                for t in self.tasks:
                    if t['name'] == task_name:
                        task_status = t['status']
                        break
                
                text = f"[任务]\n{task_name}"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if task_status == "Completed":
                    item.setBackground(QColor(200, 255, 200))
                else:
                    item.setBackground(QColor(176, 224, 230)) # 淡蓝色 (Powder Blue)
                
                item.setForeground(QColor(0, 0, 0)) # 强制黑色字体保证清晰度
                item.setData(Qt.ItemDataRole.UserRole, "task")
                self.schedule_table.setItem(period, day, item)
                
    def on_schedule_clicked(self, row, column):
        # 单击事件：如果是课程，显示详细信息
        item = self.schedule_table.item(row, column)
        if item and item.data(Qt.ItemDataRole.UserRole) == "locked":
            details = item.data(Qt.ItemDataRole.UserRole + 1)
            QMessageBox.information(self, "课程详细信息", details)
            
    def on_schedule_double_clicked(self, row, column):
        # 双击事件：安排或移除任务
        item = self.schedule_table.item(row, column)
        
        if item and item.data(Qt.ItemDataRole.UserRole) == "locked":
            # 课程双击不作处理，单击已有提示
            return
            
        if item and item.data(Qt.ItemDataRole.UserRole) == "task":
            # 取消安排
            reply = QMessageBox.question(self, "取消任务安排", "确定要将该任务移出当前的时间段吗？", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                key = (self.viewing_week, column, row)
                str_key = str(key)
                
                if key in self.schedule_assignments:
                    del self.schedule_assignments[key]
                elif str_key in self.schedule_assignments:
                    del self.schedule_assignments[str_key]
                else:
                    for k in list(self.schedule_assignments.keys()):
                        if str(k) == str_key:
                            del self.schedule_assignments[k]
                            
                self.save_data()
                self.reload_and_refresh()
            return
            
        # 安排新任务
        dialog = TaskAssignmentDialog(self.tasks, self)
        if dialog.exec():
            task_name = dialog.selected_task
            # 修复点：确保存为真实的元组整型 key
            key = (int(self.viewing_week), int(column), int(row))
            self.schedule_assignments[key] = task_name 
            self.save_data()
            self.reload_and_refresh()

    def clear_schedule_tasks(self):
        reply = QMessageBox.warning(self, "清空确认", f"确定清空 第{self.viewing_week}周 课表上所有已安排的任务吗？\n(任务列表中的任务自身不会被删除)", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            keys_to_del = []
            for k in self.schedule_assignments.keys():
                # k 可能是字符串格式："(week, day, period)"
                try:
                    if isinstance(k, str):
                        w = int(k.strip('()').split(',')[0])
                    else:
                        w = k[0]
                        
                    if w == self.viewing_week:
                        keys_to_del.append(k)
                except Exception:
                    pass
                    
            for k in keys_to_del:
                del self.schedule_assignments[k]
                
            self.save_data()
            self.reload_and_refresh()

    def load_data(self):
        # 如果读取失败或者没有数据，默认回退到硬编码默认课表
        self.courses = list(DEFAULT_COURSE_SCHEDULE)
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    raw_schedule = data.get("schedule", {})
                    # 获取课程数据
                    loaded_courses = data.get("courses")
                    if loaded_courses is not None:
                        self.courses = loaded_courses
                        
                    self.preferences = data.get("preferences", {"font_family": "微软雅黑", "font_size": 12})

                        
                    # 转换回元组字典键或直接兼容处理
                    self.schedule_assignments = {}
                    for k_str, val in raw_schedule.items():
                        parts = k_str.strip('()').split(',')
                        if len(parts) == 2:
                            # 迁移旧数据格式 "(day, period)" 到当前周 "(week, day, period)"
                            new_k = (self.current_week, int(parts[0]), int(parts[1]))
                            self.schedule_assignments[new_k] = val
                        elif len(parts) == 3:
                            new_k = (int(parts[0]), int(parts[1]), int(parts[2]))
                            self.schedule_assignments[new_k] = val
            except Exception as e:
                print(f"Error loading data: {e}")

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding='utf-8') as f:
                # 转换格式存储
                str_schedule = {}
                for k, v in self.schedule_assignments.items():
                    str_schedule[str(k)] = v
                    
                json.dump({
                    "tasks": self.tasks,
                    "schedule": str_schedule,
                    "courses": self.courses
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

class StartupLoader(QThread):
    """虚拟加载线程，用于展示进度条动画进度"""
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    
    def run(self):
        import time
        # 模拟应用加载依赖、模块的时间碎片
        for i in range(1, 101):
            time.sleep(0.015) # 约 1.5秒缓冲时间
            self.progress.emit(i)
        self.finished.emit()

class ModernSplashScreen(QSplashScreen):
    """带进度条的现代化加载启动页"""
    def __init__(self):
        # 纯代码绘制一个无边框、扁平风的启动底图
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景
        painter.setBrush(QColor(245, 250, 252))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 500, 300, 20, 20)
        
        # 主盖板
        painter.setBrush(QColor(176, 224, 230)) # Poweder Blue
        painter.drawRoundedRect(0, 0, 500, 180, 20, 20)
        
        # 标题文字
        painter.setPen(QColor(0, 0, 0))
        font = QFont("Arial", 26, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, 0, 0, -120), Qt.AlignmentFlag.AlignCenter, "BUAA Time Manager")
        
        font.setPointSize(12)
        font.setWeight(QFont.Weight.Normal)
        painter.drawText(pixmap.rect().adjusted(0, 80, 0, -120), Qt.AlignmentFlag.AlignCenter, "Spring 2026 Edition")
        
        painter.end()
        super().__init__(pixmap)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.addStretch()
        
        # 进度条
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
            QProgressBar::chunk {
                background-color: #4682B4; 
                border-radius: 6px;
            }
        """)
        self.progressBar.setTextVisible(False) # 隐藏数字让它看起来更干净
        
        # 状态文字
        self.statusLabel = QLabel("Initializing Environment...")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.setStyleSheet("color: #666666; font-family: Arial; font-size: 12px; margin-bottom: 30px;")
        
        layout.addWidget(self.progressBar)
        layout.addWidget(self.statusLabel)
        
    def updateProgress(self, value):
        self.progressBar.setValue(value)
        if value < 30:
            self.statusLabel.setText("正在加载依赖项库...")
        elif value < 70:
            self.statusLabel.setText("正在配置周课表环境...")
        elif value < 95:
            self.statusLabel.setText("正在读取本地任务存储与记录...")
        else:
            self.statusLabel.setText("启动就绪，准备加载界面...")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 实例化加载页并居中展示
    splash = ModernSplashScreen()
    splash.show()
    
    # 全局变量或容器以便能在加载完毕后呈现
    window = None
    
    def start_main_window():
        global window
        window = BUAA_TimeManager()
        window.show()
        splash.finish(window)
        
    # 开一个虚拟线程控制加载动画条，走完后再拉起主程序
    loader = StartupLoader()
    loader.progress.connect(splash.updateProgress)
    loader.finished.connect(start_main_window)
    loader.start()
    
    sys.exit(app.exec())
