# -*- coding: utf-8 -*-
__title__   = "Обновить\nплощадь"
__doc__ = """
Обновляет замороженную площадь помещений.  
  
Режимы работы:
- Обновить у всех помещений
- Обновить у выбранных помещений
- Обновить у всех помещений выбранной группы
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
                          Separator, Button, CheckBox, ComboBox)

from config import configs, apartutils
from functions.customselection import CustomSelections
from collections import defaultdict


#==================================================
#MAIN
#==================================================
doc, uidoc, app = configs.get_context()
doc_title = doc.Title

#Rooms
components = [
    Label('Выберете режим работы:'),
    ComboBox('mode', {'Все помещения': 1, 
                      'Выбранные помещения': 2, 
                      "Все помещения выбранной группы": 3
                      }),
    Button('Подтвердить')
]

form = FlexForm('Преднастройка', components)
form.show()

if form.values:
    mode = form.values['mode']

    if mode == 1:
        rooms = FilteredElementCollector(doc) \
        .OfCategory(BuiltInCategory.OST_Rooms) \
        .ToElements()
    elif mode == 2:
        rooms = CustomSelections.pick_elements_by_category(built_in_category=BuiltInCategory.OST_Rooms, 
                                                                status="Выберете помещения для перерасчета площади"
                                                                )
    elif mode == 3:
        base_group = configs.RoomItem(CustomSelections.pick_element_by_category(built_in_category=BuiltInCategory.OST_Rooms, 
                                                                    status="Выберете ОДНО помещение нужной вам группы"
                                                                    ))
        
        rooms = apartutils.get_group_by_room(doc, base_group).get("rooms")

    rooms = configs.wrap_in_room_item(rooms)
    with Transaction(doc, 'Rooms_Обновление площадей') as t:
        t.Start()
        for room in rooms:
            area = room.rounded_area
            room.ps_area_frozen.Set(area)
        t.Commit()
