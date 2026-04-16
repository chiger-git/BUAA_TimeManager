import sys
import json

filepath = "TimeManager.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Version
content = content.replace('CURRENT_VERSION = "1.1.0"', 'CURRENT_VERSION = "1.0.1"')
content = content.replace('CURRENT_VERSION = "1.0.0"', 'CURRENT_VERSION = "1.0.1"') # just in case

# 2. Fix the week calculation: "默认显示的周数会比实际时间晚一周" usually means it displays a week number that is 1 lower, or it shifts one week late. We change 1 to 2.
# If they mean "it shows week 6 when it should be week 5", changing +1 to 0 or -1 would be correct. But mathematically `days//7 + 1` is standard. Let's do delta.days // 7 + 2 if we assume it's behind.
# Actually, wait. "比实际时间晚一周" - e.g. "my watch is 1 hour late", it means "it shows 4:00 when it is 5:00". So it is behind. So we ADD 1 to fix it.
content = content.replace("week = delta.days // 7 + 1", "week = delta.days // 7 + 2")

# 3. Add SelectionMode for task_table
selection_behavior = "self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)"
extended_selection = selection_behavior + "\n        self.task_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)"
if "ExtendedSelection" not in content:
    content = content.replace(selection_behavior, extended_selection)

# 4. Modify delete_task
delete_task_old = """    def delete_task(self):
        selected_rows = [item.row() for item in self.task_table.selectedItems()]
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先点选选中一行任务，然后再点击删除。")
            return

        row = selected_rows[0]
        task_name = self.task_table.item(row, 0).text()

        # 删除任务并从课表关联中清理
        self.tasks = [t for t in self.tasks if t['name'] != task_name]"""

delete_task_new = """    def delete_task(self):
        selected_rows = list(set([item.row() for item in self.task_table.selectedItems()]))
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先点选选中一行或多行任务，然后再点击删除。")
            return

        task_names = [self.task_table.item(row, 0).text() for row in selected_rows]

        # 删除任务并从课表关联中清理
        self.tasks = [t for t in self.tasks if t['name'] not in task_names]"""
content = content.replace(delete_task_old, delete_task_new)

# 5. Modify toggle_task_status
toggle_status_old = """    def toggle_task_status(self):
        selected_rows = [item.row() for item in self.task_table.selectedItems()]
        if not selected_rows:
            return

        row = selected_rows[0]
        task_name = self.task_table.item(row, 0).text()

        for task in self.tasks:
            if task['name'] == task_name:
                task['status'] = "Completed" if task['status'] == "Pending" else "Pending"
                break

        self.save_data()"""

toggle_status_new = """    def toggle_task_status(self):
        selected_rows = list(set([item.row() for item in self.task_table.selectedItems()]))
        if not selected_rows:
            return

        task_names = [self.task_table.item(row, 0).text() for row in selected_rows]

        for task in self.tasks:
            if task['name'] in task_names:
                task['status'] = "Completed" if task['status'] == "Pending" else "Pending"

        self.save_data()"""

content = content.replace(toggle_status_old, toggle_status_new)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# Optional: verify the change logic
