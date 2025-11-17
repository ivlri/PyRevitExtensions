# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
from System.IO import StreamWriter
import System.Text
from Autodesk.Revit.UI import *
from pyrevit import revit
import inspect


class ToolLogger(object):
    def __init__(self, log_path=None, script_path=None, tool_name=None):
        # Текущий год и месяц
        now = datetime.now()
        log_filename = "log_{:02d}_{:02d}.xml".format(now.month, now.year)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # две папки вверх
        default_log_dir = os.path.join(base_dir, "logs")

        # Убедиться, что папка существует
        if not os.path.exists(default_log_dir):
            try:
                os.makedirs(default_log_dir)
            except:
                pass  # Без выброса ошибки

        self.log_path = log_path or os.path.join(default_log_dir, log_filename)

        
        # Имя инструмента — по умолчанию из названия папки скрипта
        if tool_name:
            self.tool_name = tool_name
        elif script_path:
            folder_name = os.path.basename(os.path.dirname(script_path))
            self.tool_name = folder_name.split('.')[0]
        else:
            self.tool_name = "UnknownTool"

        # Имя пользователя из Revit
        # self.user_name = revit.doc.Application.Username

        ui_app = UIApplication(__revit__.Application)  
        self.user_name = ui_app.Application.Username

    def log(self):
        try:
            # --- Список пользователей, которых не нужно логировать
            excluded_users = ["Legostaev", "testuser"]

            # --- Пропуск логирования для исключённых
            if self.user_name.lower() in [u.lower() for u in excluded_users]:
                return

            # --- Создание XML, если не существует
            if not os.path.exists(self.log_path):
                root = ET.Element("Log")
                tree = ET.ElementTree(root)
                tree.write(self.log_path, encoding="utf-8", xml_declaration=True)

            # --- Загрузка и добавление записи
            tree = ET.parse(self.log_path)
            root = tree.getroot()

            log_entry = ET.SubElement(root, "Entry")
            log_entry.set("User", self.user_name)
            log_entry.set("Tool", self.tool_name)
            log_entry.set("Date", datetime.now().strftime("%d.%m.%Y"))
            log_entry.set("Time", datetime.now().strftime("%H:%M"))

            # --- Красивый вывод и запись через .NET
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = "\n".join([line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip()])

            with StreamWriter(self.log_path, False, System.Text.Encoding.UTF8) as f:
                f.Write(pretty_xml)

        except Exception as e:
            print("⚠️ Ошибка логирования:", e)


# Добавляем логирование использования инструмента
#import os
#from functions._logger import ToolLogger
#ToolLogger(script_path=__file__).log()