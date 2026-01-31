# -*- coding: utf-8 -*-
__title__   = "Обновить\nэтаж"
__doc__ = """Описание: Обновляет значения этажа в номерах квартир и помещений.
Не пересчитывает параметры помещений. Используется после копирования типового этажа."""

#==================================================
# IMPORTS
#==================================================

import os
import clr
import sys
import traceback

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

from pyrevit import forms

from config import configs, apartutils
from functions.customselection import CustomSelections

#==================================================
# MAIN
#==================================================
doc, uidoc, app = configs.get_context()
doc_title = doc.Title

rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
rooms = configs.wrap_in_room_item(rooms)

gp_code, section_value = apartutils.get_section(doc)

floor_index = 1 if section_value else 0

updated_count = 0
errors = []

with Transaction(doc, "Rooms_Обновление этажа") as t:
    t.Start()
    
    for room in rooms:
        try:
            level_value = apartutils.get_level(room)
            if level_value is None:
                continue
            
            apart_numb = room.adsk_apart_numb.AsValueString() or ""
            room_numb = room.adsk_room_numb.AsValueString() or ""
            
            if not apart_numb or not room_numb:
                continue
            
            apart_parts = apart_numb.split(".")
            if len(apart_parts) > floor_index:
                existing = apart_parts[floor_index]
                level_str = str(level_value).zfill(len(existing)) if existing.isdigit() else str(level_value)
                apart_parts[floor_index] = level_str
                new_apart_numb = ".".join(apart_parts)
                room.adsk_apart_numb.Set(new_apart_numb)
            

            room_parts = room_numb.split(".")
            if len(room_parts) > floor_index:
                existing = room_parts[floor_index]
                level_str = str(level_value).zfill(len(existing)) if existing.isdigit() else str(level_value)
                room_parts[floor_index] = level_str
                new_room_numb = ".".join(room_parts)
                room.adsk_room_numb.Set(new_room_numb)
            
            updated_count += 1
            
        except Exception as ex:
            room_id = room.Id.ToString() if hasattr(room, 'Id') else "Unknown"
            errors.append("Ошибка в помещении {room_id}: {}".format(room_id, str(ex)))
            continue
    
    t.Commit()

# Отчет
if errors:
    message = "Завершено с ошибками:\nОбновлено: {} помещений\nОшибки:\n{}".format(
        updated_count, "\n".join(errors[:5])
    )
    forms.alert(message, title="Предупреждение", warn_icon=True)
else:
    forms.alert("Успешно обновлено {} помещений".format(updated_count), title="Готово")