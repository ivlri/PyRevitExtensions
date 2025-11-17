# -*- coding: utf-8 -*-

import os
import codecs

def remove_recent_files_from_ini(ini_file_path):
    # Проверка существования файла
    if not os.path.exists(ini_file_path):
        return

    # Чтение файла с учетом BOM
    with codecs.open(ini_file_path, 'r', encoding='utf-16') as file:
        content = file.read()

    # Разбиваем содержимое на строки
    lines = content.splitlines(keepends=True)

    # Поиск секции [Recent File List]
    for i, line in enumerate(lines):
        if '[Recent File List]' in line:
            lines = lines[:i]  # Оставляем только строки до [Recent File List]
            break

    # Убираем лишние пустые строки в конце
    while lines and lines[-1].strip() == '':
        lines.pop()

    # Перезаписываем файл в кодировке UTF-16 LE с BOM
    with codecs.open(ini_file_path, 'w', encoding='utf-16') as file:
        file.writelines(lines)

# Получаем путь к файлу Revit.ini с использованием переменной окружения %appdata%
ini_file_path = os.path.join(os.getenv('APPDATA'), 'Autodesk', 'Revit', 'Autodesk Revit 2022', 'Revit.ini')

# Вызов функции
remove_recent_files_from_ini(ini_file_path)
