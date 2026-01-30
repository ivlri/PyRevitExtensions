# -*- coding: utf-8 -*-
__title__   = "Квартиро-\nграфия"
__doc__ = """
Описание: Производит расчет квартировграфии
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
components = [
    Label('Выберете режим расчета:'),
    ComboBox('mode', {'Все квартиры': 1, 
                      'Одну на выбор': 2,
                      }),
    Button('Подтвердить')
]

form = FlexForm('Преднастройка', components)
form.show()
mode = form.values['mode']

#Rooms
if mode == 1:
    sorted_items = apartutils.get_sorted_live_rooms(doc)
else:
    items = apartutils.get_group_by_room(doc=doc)
    r = configs.wrap_in_room_item(items.get('rooms'))
    sorted_items = [(items.get('index'), r)]


with Transaction(doc, "Rooms_Расчет квартирографии") as t:
    t.Start()
    try:
        for _, rooms in sorted_items:

            # --- агрегаты квартиры ---
            adsk_area_live = 0.0              # жилая площадь
            adsk_area = 0.0                   # площадь теплого контура
            ps_area_without_coef = 0.0        # площадь без коэффициента
            adsk_area_with_coef = 0.0         # площадь с коэффициентом
            ps_area_summer = 0.0              # летние помещения
            live_room_count = 0               # количество жилых комнат
            is_stud = False
            check = 0
            # --- проверка коэффициентов (один раз - перезапись) ---
            if any(room.adsk_coef.AsDouble() == 0 for room in rooms):
                r, area_coefs, _, _ = apartutils.sorted_rooms(rooms, "Жилье")
                for r_room, coef in zip(r, area_coefs):
                    r_room.adsk_coef.Set(coef)

            # --- расчет ---
            for room in rooms:
                check_try_area = room.element.LookupParameter('Площадь').AsDouble()
                if check_try_area == 0:
                    check += 1

                group = room.ps_group.AsValueString()
                coef = room.adsk_coef.AsDouble()
                area = room.ps_area_frozen.AsDouble()

                adsk_area_with_coef += area * coef
                ps_area_without_coef += area

                if group == "Летнее":
                    ps_area_summer += area
                else:
                    adsk_area += area

                if room.Name in configs.RoomItem.LIVING_NAMES:
                    live_room_count += 1
                    adsk_area_live += area

                # --- сразу отметить студии ---
                if room.Name in configs.RoomItem.STUD:
                    is_stud = True

            if check > 0:
                forms.alert("Расчет принудительно остановлен!", sub_msg="Найдено неразмещенных помещений: {}\nИсправьте неразмещенные помещения что бы сделать расчет".format(check))
                sys.exit()
            # --- тип квартиры ---
            adsk_apart_type = "{}С".format(live_room_count) if not is_stud else "С"

            # --- запись параметров ---
            for room in rooms:
                room.adsk_area_live.Set(adsk_area_live)
                room.adsk_area.Set(adsk_area)
                room.ps_area_without_coef.Set(ps_area_without_coef)
                room.adsk_area_with_coef.Set(
                    configs.RoomItem.round_area(adsk_area_with_coef)
                )
                room.ps_area_summer.Set(ps_area_summer)
                room.adsk_apart_type.Set(adsk_apart_type)

                if is_stud:
                    room.room_description.Set('Студия')

    except Exception:
        print(traceback.format_exc())
    finally:
        t.Commit()
