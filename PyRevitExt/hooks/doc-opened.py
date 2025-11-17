# -*- coding: utf-8 -*-
from pyrevit import forms, revit, forms
import os
import System.Windows.Forms as WinForms
import datetime
from Autodesk.Revit.DB import ModelPathUtils

# Указываем путь к целевой папке
root_folder = r"\\fs\bim\Projects\00.BIM_Export\Проверки на пересечения"

# Список папок для игнорирования
ignore_folders = ["тест", "тест2"]

# Получаем текущий документ Revit
doc1 = revit.doc

# Получаем имя текущего пользователя
current_user = doc1.Application.Username

# Список пользователей, для которых предупреждение не показывается
allowed_users = ["legostaev!", "chernova.a!", "medvedev!", "stepanova", "sivkova", "pitkina", "mitchishnina", "chernova_ps", "baranov", "suvorova"]

# Если пользователь находится в списке разрешенных, не выводим предупреждение
if current_user not in allowed_users:
    # Получаем путь к центральному файлу, если документ совместной работы
    if doc1.IsWorkshared:
        central_path = ModelPathUtils.ConvertModelPathToUserVisiblePath(doc1.GetWorksharingCentralModelPath())
    else:
        central_path = doc1.PathName

    # Извлекаем только имя текущего файла Revit без расширения
    current_revit_file = os.path.splitext(os.path.basename(central_path))[0] if central_path else ""

    # Проверка доступа к папке
    if os.path.exists(root_folder):
        # Создаем словарь для хранения найденных XML-файлов и их путей
        xml_file_paths = {}

        # Сканируем корневую папку и первую вложенность
        for folder_name in os.listdir(root_folder):
            folder_path = os.path.join(root_folder, folder_name)

            # Проверяем, является ли это папкой и не входит ли она в список игнорируемых
            if os.path.isdir(folder_path) and folder_name not in ignore_folders:
                # Ищем XML-файлы в подпапках
                xml_files = [f for f in os.listdir(folder_path) if f.endswith(".xml")]
                for xml_file in xml_files:
                    # Сохраняем путь к XML-файлу в словаре с именем файла без расширения
                    file_name_without_extension = os.path.splitext(xml_file)[0]
                    xml_file_paths[file_name_without_extension] = os.path.join(folder_path, xml_file)

        # Проверка на совпадение имен
        if current_revit_file in xml_file_paths:
            # Получаем путь к соответствующему XML-файлу
            xml_file_path = xml_file_paths[current_revit_file]

            # Получаем дату создания XML-файла
            creation_time = os.path.getctime(xml_file_path)

            # Преобразуем время в читаемый формат (день месяц год)
            creation_time_str = datetime.datetime.fromtimestamp(creation_time).strftime('%d.%m.%Y')

            # Вывод предупреждения, если совпадение найдено
            forms.alert("Для текущего файла '{0}' есть проверка на пересечения от {1}".format(current_revit_file, creation_time_str))
            # WinForms.MessageBox.Show(
            #     "Для текущего файла '{0}' есть проверка на пересечения от {1}".format(current_revit_file, creation_time_str),
            #     "Предупреждение",
            #     WinForms.MessageBoxButtons.OK,
            #     WinForms.MessageBoxIcon.Warning
            # )
