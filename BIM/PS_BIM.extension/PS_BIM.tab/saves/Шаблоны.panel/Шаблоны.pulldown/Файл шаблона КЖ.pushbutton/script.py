# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult

# Папка, в которой нужно искать файлы
folder_path = r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\KR_Арматура и жб'

def find_latest_rvt_file(folder):
    """Находит последний по дате файл с расширением .rvt, исключая резервные копии."""
    rvt_files = []
    
    # Проходим по всем файлам в папке
    for file_name in os.listdir(folder):
        # Проверяем, что это файл .rvt и он не является резервной копией
        if file_name.endswith('.rvt') and not re.search(r'\d{4}$', file_name):
            # Получаем полный путь к файлу
            full_path = os.path.join(folder, file_name)
            # Получаем время последнего изменения файла
            file_time = os.path.getmtime(full_path)
            # Добавляем в список файл и его время изменения
            rvt_files.append((full_path, file_time))

    if not rvt_files:
        return None
    
    # Находим файл с самым последним временем изменения
    latest_file = max(rvt_files, key=lambda x: x[1])
    return latest_file[0]

def open_and_activate_document(uiapp, rvt_file_path):
    """Открывает и активирует файл шаблона в текущей сессии Revit."""
    
    # Проверяем, существует ли файл
    if os.path.exists(rvt_file_path):
        # Открываем и активируем документ
        uidoc = uiapp.OpenAndActivateDocument(rvt_file_path)
        
        if uidoc:
            pass  # Успешное открытие файла, ничего не выводим
        else:
            pass  # Не удалось открыть файл, ничего не выводим
    else:
        pass  # Файл не существует, ничего не выводим

# Ищем последний файл
latest_rvt_file = find_latest_rvt_file(folder_path)

if latest_rvt_file:
    # Получаем только имя файла, без пути
    latest_rvt_file_name = os.path.basename(latest_rvt_file)
    
    # Создаем диалоговое окно с предупреждением и именем файла
    dialog = TaskDialog("Предупреждение")
    dialog.MainInstruction = "Вы открываете файл шаблона: {}. Вы уверены?".format(latest_rvt_file_name)
    dialog.CommonButtons = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No  # Кнопки Да/Нет
    dialog.DefaultButton = TaskDialogResult.No  # Кнопка по умолчанию — "Нет"

    # Показываем диалог и получаем результат
    result = dialog.Show()

    # Если пользователь нажал "Да", открываем файл в Revit
    if result == TaskDialogResult.Yes:
        open_and_activate_document(__revit__, latest_rvt_file)
    else:
        pass  # Открытие файла отменено, ничего не выводим
else:
    print("Файл не найден.")
