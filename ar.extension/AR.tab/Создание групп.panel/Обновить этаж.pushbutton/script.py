# -*- coding: utf-8 -*-
__title__   = "Обновить\nэтаж"
__doc__ = """Описание:  Не перерасчитывает параметры помещений!!!
Обновляет значения связанные с этажем. Нужно для того что бы не собирать повторно группу при копировании типового этажа."""
#==================================================
#IMPORTS
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
#MAIN
#==================================================
doc, uidoc, app = configs.get_context()
doc_title = doc.Title

#Rooms
rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
rooms = configs.wrap_in_room_item(rooms)

gp_code, section_value = apartutils.get_section(doc)

with Transaction(doc, "Rooms_Обновление этажа") as t:
    t.Start()

    for room in rooms:
        level_value = apartutils.get_level(room)

        apart_numb = room.adsk_apart_numb.AsValueString()
        room_numb = room.adsk_room_numb.AsValueString()

        rep_index = room_numb.split(".")[2] if section_value else 0

        apart_numb[rep_index] = level_value
        room_numb[rep_index] = level_value

        room.adsk_apart_numb.Set(apart_numb)
        room.adsk_room_numb.Set(room_numb)


