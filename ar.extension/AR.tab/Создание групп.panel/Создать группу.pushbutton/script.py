# -*- coding: utf-8 -*-
__title__   = 'Создать\nгруппу'
__doc__ = 'Описание: Собирает помещения в единую группу '
#==================================================
#IMPORTS
#==================================================

import os
import clr
import sys
import re
import traceback

from tempfile import gettempdir

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.UI import *

from pyrevit import forms
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button, CheckBox)
from config import configs, apartutils

from functions.customselection import CustomSelections

#=========================================================
#Functions
#=========================================================

def resolve_gp_inputs(is_numeric, gp_code, section_value):
    '''
    Определяет:
    - нужен ли номер квартиры
    - нужен ли ручной ввод gp
    '''
    need_room_index = is_numeric
    need_gp_manual = is_numeric and not gp_code
    return need_room_index, need_gp_manual

def ask_gp_values(need_room_index, need_gp_manual, alert):
    components = []

    if need_room_index:
        components.extend([
            Label('Укажите номер квартиры на этаже'),
            TextBox('room_index'),
            CheckBox('alert', 'Вывести сводку по группе?',default=alert)
        ])

    if need_gp_manual:
        components.extend([
            Separator(),
            Label('Введите код секции (ГП)'),
            TextBox('gp_code')
        ])

    if not components:
        return "", True, None
    
    components.append(Button('Подтвердить'))

    form = FlexForm('Преднастройка', components)
    form.show()

    room_index = form.values.get('room_index', '')
    use_alert = form.values.get('alert', None)

    return room_index, use_alert, form

def build_gp_value(form, gp_code, section_value):
    if gp_code:
        return 'ГП{}-С{}'.format(gp_code, section_value)

    return form.values.get('gp_code')

#==================================================
#MAIN
#==================================================
try:
    doc, uidoc, app = configs.get_context()
    doc_title = doc.Title
    temp_alert = configs.rb_temp()

    #Rooms
    selected_rooms = CustomSelections.pick_elements_by_category(built_in_category=BuiltInCategory.OST_Rooms, 
                                                                status='Выберете помещения для создания группы'
                                                                )

    if selected_rooms:
        selected_rooms = configs.wrap_in_room_item(selected_rooms)
        apart_type, is_numeric = apartutils.get_apart_type(selected_rooms)

        if apart_type is None:
            forms.alert('Выбраны разные по типу помещения! Выбирайте за раз помещения одного типа.')
            sys.exit()

        room_index = ''
        gp_value = ''
        gp_code, section_value = apartutils.get_section(doc)

        need_room_index, need_gp_value = resolve_gp_inputs(
            is_numeric, gp_code, section_value
        )

        room_index, use_alert, form = ask_gp_values(need_room_index, need_gp_value, temp_alert)
            
        if apart_type in ['Жилье', 'Ритейл']:
            if use_alert != temp_alert:
                configs.rb_temp(use_alert)
                temp_alert = use_alert
        else:
            temp_alert = True

        gp_value = build_gp_value(form, gp_code, section_value)

        sorted_rooms, coef_values, ps_groups, ps_purposes = apartutils.sorted_rooms(selected_rooms, 
                                                                                    apart_type)
        
        alert, sub_msg = apartutils.create_new_group(doc=doc, 
                                                    tr_name='Rooms_Сбор группы',
                                                    rooms=sorted_rooms, 
                                                    coef_values=coef_values, 
                                                    ps_groups=ps_groups, 
                                                    ps_purposes=ps_purposes, 
                                                    room_index=room_index,
                                                    gp_code=gp_value, 
                                                    section_value=section_value,
                                                    alert=temp_alert)


except Exception:
    print(traceback.format_exc())