# -*- coding: utf-8 -*-
__title__   = "Номер\nв доме"
__doc__ = """
Описание: Заполняет порядковый номер в доме - начинает с веденного числа заканчивает 
в числом квартир в секции.

Как использовать: после запуска вас попросят ввести начальный номер квартиры в секции (для каждой секции вводите свое значение).  
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


#UI
components = [
    Label('Укажите начальный номер'), 
    TextBox('number'),
    Button('Подтвердить')
]

form = FlexForm('Преднастройка', components)
form.show()
if form.values:
    #Rooms
    sorted_items = apartutils.get_sorted_live_rooms(doc)
    
    start_numb = int(form.values['number'])

    #Generator
    apart_numbers = [str(i) for i in range(start_numb, len(sorted_items) + start_numb)]
    with Transaction(doc, 'Rooms_Порядковый номер в доме') as t:
        t.Start()
        for sorted_item, apart_number in zip(sorted_items, apart_numbers):
            key, rooms = sorted_item
            for room in rooms:
                room.adsk_numb_in_home.Set(apart_number)
        t.Commit()

    print(apart_numbers)
    forms.alert("Заполнение номера завершено",
                sub_msg="Начальный номер - {}\nКонечный номер - {}"\
                    .format(apart_numbers[0],apart_numbers[-1]))
