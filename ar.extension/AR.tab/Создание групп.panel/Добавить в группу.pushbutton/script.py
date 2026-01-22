# -*- coding: utf-8 -*-
__title__   = "Добавить\nв группу"
__doc__ = "Описание: Добавляет помещение в уже созданную группу"
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
r_to_add = CustomSelections.pick_elements_by_category(built_in_category=BuiltInCategory.OST_Rooms, 
                                                            status="Выберете помещения которые нужно добавить в группу"
                                                            )

base_group = configs.RoomItem(CustomSelections.pick_element_by_category(built_in_category=BuiltInCategory.OST_Rooms, 
                                                            status="Выберете ОДНО помещение нужной вам группы"
                                                            ))


group_items  = apartutils.get_group_by_room(doc, base_group)
selected_rooms = configs.wrap_in_room_item(group_items.get("rooms")) + configs.wrap_in_room_item(r_to_add)

apart_type, is_numeric = apartutils.get_apart_type(selected_rooms)

if apart_type is None:
    forms.alert("Выбраны разные по типу помещения! Выбирайте за раз помещения одного типа.")
    sys.exit()

# Основной процесс
gp_code, section_value = apartutils.get_section(doc)

rooms, coef_values, ps_groups, ps_purposes = apartutils.sorted_rooms(selected_rooms, apart_type)

alert, sub_msg = apartutils.create_new_group(doc=doc, 
                                             tr_name = "Rooms_Добавить в группу",
                                             rooms=rooms, 
                                             coef_values=coef_values, 
                                             ps_groups=ps_groups, 
                                             ps_purposes=ps_purposes, 
                                             room_index=group_items.get("index"),
                                             gp_code=group_items.get("gp"), 
                                             section_value=section_value)


