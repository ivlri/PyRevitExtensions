# -*- coding: utf-8 -*-
__title__   = "Перерасчет\nгрупп"
__doc__ = """
Перерасчет групп после удаления помещений  

Когда запускать: Только при массовом удалении помещений из групп. Скрипт сам соберет ОСТАВШИЕСЯ группы и пересчитает ВСЕ параметры этих групп.  
Для добавления новых помещений в группу — используйте "Добавить в группу".
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
sorted_items = apartutils.get_sorted_live_rooms(doc)

components = [
    CheckBox('is_set_area', 'Пересчитать замороженную площадь?', default=True),
    Button('Подтвердить')
]

form = FlexForm('Преднастройка', components)
form.show()

if form.values:
    is_set_area = form.values['is_set_area']

    with Transaction(doc, 'Rooms_Перерасчет групп') as t:
        t.Start()

        for index, grouped_rooms in sorted_items:
            try:
                first_room = grouped_rooms[0]
                apart_type = first_room.ps_purpose.AsValueString()

                rooms, coef_values, ps_groups, ps_purposes = apartutils.sorted_rooms(grouped_rooms, apart_type)
                alert, sub_msg = apartutils.create_new_group(doc=doc, 
                                                            rooms=rooms, 
                                                            coef_values=coef_values, 
                                                            ps_groups=ps_groups, 
                                                            ps_purposes=ps_purposes, 
                                                            room_index=first_room.adsk_index.AsValueString(),
                                                            gp_code=first_room.adsk_section_str.AsValueString(), 
                                                            section_value=first_room.ps_section_numb.AsValueString(),
                                                            set_frozen_area=is_set_area,
                                                            alert=False
                                                            )
            except Exception:
                print(traceback.format_exc())
                break

        t.Commit()
