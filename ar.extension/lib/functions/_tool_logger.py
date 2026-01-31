# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
from System.IO import StreamWriter
import System.Text
from pyrevit import revit


class ToolLogger(object):
    def __init__(self, log_path=None, tool_name=None):
        # Путь к XML-файлу по умолчанию
        self.log_path = log_path or r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\05_Программы\06_PS_Panels_PyRevit\ALL\PS_ALL.extension\PS_ALL.tab\tool_log.xml"
        
        # Имя инструмента — по умолчанию из названия папки
        if tool_name:
            self.tool_name = tool_name
        else:
            folder_name = os.path.basename(os.path.dirname(__file__))
            self.tool_name = folder_name.split('.')[0]

        # Имя пользователя из Revit
        self.user_name = revit.doc.Application.Username

    def log(self):
        try:
            # Создание XML, если не существует
            if not os.path.exists(self.log_path):
                root = ET.Element("Log")
                tree = ET.ElementTree(root)
                tree.write(self.log_path, encoding="utf-8", xml_declaration=True)

            # Загрузка и добавление записи
            tree = ET.parse(self.log_path)
            root = tree.getroot()

            log_entry = ET.SubElement(root, "Entry")
            log_entry.set("User", self.user_name)
            log_entry.set("Tool", self.tool_name)
            log_entry.set("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Красивый вывод и запись через .NET
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = "\n".join([line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip()])

            with StreamWriter(self.log_path, False, System.Text.Encoding.UTF8) as f:
                f.Write(pretty_xml)

        except Exception as e:
            print("⚠️ Ошибка логирования:", e)

