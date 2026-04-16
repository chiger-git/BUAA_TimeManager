import os

file_path = r'D:\2026_Spring\TimeManageTools\TimeManager.py'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Replace the messy data with clean valid syntax
import re

start_idx = text.find('TIMETABLE = [')
end_idx = text.find('class ', start_idx)

if start_idx != -1 and end_idx != -1:
    clean_replacement = '''TIMETABLE = []
DEFAULT_COURSE_SCHEDULE = []
'''
    new_text = text[:start_idx] + clean_replacement + text[end_idx:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Fixed corrupted header!")
else:
    print("Could not find the target sections:", start_idx, end_idx)
