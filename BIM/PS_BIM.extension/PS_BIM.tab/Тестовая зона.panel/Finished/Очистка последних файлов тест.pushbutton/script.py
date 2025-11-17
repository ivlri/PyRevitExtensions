# -*- coding: utf-8 -*-

import os
import codecs

def remove_recent_files_from_ini(ini_file_path):
    if not os.path.exists(ini_file_path):
        return
    with codecs.open(ini_file_path, 'r', encoding='utf-16') as file:
        content = file.read()

    lines = content.splitlines(keepends=True)

    for i, line in enumerate(lines):
        if '[Recent File List]' in line:
            lines = lines[:i]  # Оставляем только строки до [Recent File List]
            break

    while lines and lines[-1].strip() == '':
        lines.pop()

    with codecs.open(ini_file_path, 'w', encoding='utf-16') as file:
        file.writelines(lines)

# Получаем путь к файлу Revit.ini с использованием переменной окружения %appdata%
ini_file_path = os.path.join(os.getenv('APPDATA'), 'Autodesk', 'Revit', 'Autodesk Revit 2022', 'Revit.ini')

remove_recent_files_from_ini(ini_file_path)
