# -*- coding: utf-8 -*-
__title__   = "Обратить\nномера"
__doc__ = """
Описание: Обновляет параметр ADSK_Помещение квартиры для всех помещений  

Как использовать: Запускаем только в случае, если в уже готовой секции у большого количества квартир были удалены некоторые помещения.
"""

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
from rpw.ui.forms import (FlexForm, Label, TextBox,
                          Separator, Button, CheckBox)

from config import configs, apartutils
from functions.customselection import CustomSelections
from collections import defaultdict


#==================================================
#MAIN
#==================================================
doc, uidoc, app = configs.get_context()
doc_title = doc.Title

#Rooms
sorted_items = apartutils.get_sorted_live_rooms(doc, group_by_level=True)

with Transaction(doc, 'Rooms_Обратить нумерацию') as t:
    t.Start()

    for level, group in sorted_items.items():
        keys, all_rooms = zip(*group)
        rev_keys = list(keys)[::-1]
        for new_numb, rooms, old_numb in zip(rev_keys,all_rooms,keys):
            for room in rooms:
                n_room_numb = room.adsk_room_numb.AsValueString()
                
                room.adsk_apart_numb.Set(new_numb)
                room.adsk_room_numb.Set(n_room_numb.replace(old_numb, new_numb))

    t.Commit()

# forms.alert("Заполнение номера завершено",
#             sub_msg="Начальный номер - {}\nКонечный номер - {}"\
#                 .format(apart_numbers[0],apart_numbers[-1]))
