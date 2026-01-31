# -*- coding: utf-8 -*-

from config import configs
import re
import traceback
from collections import defaultdict

from pyrevit import forms
from Autodesk.Revit.DB import *
from functions.customselection import CustomSelections

#=========================================================
# Конфигурация типов помещений
#=========================================================

APART_CONFIGS = {
    'Жилье': {
        'prefix': '',
        'use_room_index': True,
        'set_room_count': True,
        'studio_if_zero': True
    },
    'Ритейл': {
        'prefix': 'P',
        'use_room_index': True
    }
}

DEFAULT_CONFIG = {
    'prefix': lambda typ: typ[0],
    'use_room_index': False,
    'set_room_count': False,
    'studio_if_zero': False
}


def get_apart_config(apart_type):
    cfg = DEFAULT_CONFIG.copy()
    cfg.update(APART_CONFIGS.get(apart_type, {}))
    return cfg


#=========================================================
# Вспомогательные функции
#=========================================================

rooms_groups = configs.get_groups()


def get_section(doc):
    pattern = re.compile(r'_GP([A-Za-z0-9.]+).*?_Rooms_(?:GP\d+_)?(\d+)')
    match = pattern.search(doc.Title or '')
    if match:
        return match.group(1), str(int(match.group(2)))
    return None, None


def get_level(room):
    layer = room.LevelName or ''
    if 'Этаж -01' in layer:
        return '-1'

    match = re.search(r'Этаж\s+(\d+)', layer)
    return str(int(match.group(1))) if match else '0'


def get_apart_type(selected_rooms):
    names = [room.Name for room in selected_rooms]

    if names.count('Кладовая') > 2:
        return 'Кладовая', False

    names_set = set(names)
    for apart_type, defs in rooms_groups.items():
        valid_names = set(item.get('Наименование') for item in defs)
        if names_set.issubset(valid_names):
            return apart_type, apart_type in ('Жилье', 'Ритейл')

    return None, False

# def check_area(rooms):
#     if isinstance(rooms[0], configs.RoomItem):
#         for 

def sorted_rooms(selected_rooms, apart_type):
    defs = rooms_groups.get(apart_type, [])
    defs_by_name = dict(
        (d.get('Наименование'), d) for d in defs
    )

    items = []
    for room in selected_rooms:
        d = defs_by_name.get(room.Name)
        if not d:
            continue

        items.append((
            d.get('PS_Приоритет в нумерации', 999),
            room,
            d.get('ADKS_Коэффициент площади', 1.0),
            d.get('PS_Группа помещений', ''),
            d.get('PS_Назначение помещений', '')
        ))
    items.sort(key=lambda x: x[0])
    _, rooms, coefs, ps_groups, ps_purposes = zip(*items)
    return rooms, coefs, ps_groups, ps_purposes

def get_group_by_room(doc, base_room=None):
    # Данные из базовой группы
    if not base_room:
        base_room = configs.RoomItem(CustomSelections.pick_element_by_category(built_in_category=BuiltInCategory.OST_Rooms, 
                                                                status="Выберете ОДНО помещение нужной вам квартиры"
                                                                ))
    room_index =base_room.adsk_index.AsValueString()
    room_numb = base_room.adsk_apart_numb.AsValueString()
    gp_value = base_room.adsk_section_str.AsValueString()

    # Сбор нужных помещений
    all_rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
    rooms_in_group = filter(lambda x: x.LookupParameter('ADSK_Номер квартиры').AsValueString() == room_numb, all_rooms)

    return {
        'rooms' : rooms_in_group,
        'index' : room_index,
        'gp' : gp_value,
    }
#=========================================================
# Формирование номеров
#=========================================================

def build_numbers(cfg, 
                  apart_type, 
                  section, 
                  start_layer,
                  layer, 
                  room_index, 
                  r_count):
    
    if callable(cfg['prefix']):
        prefix = cfg['prefix'](apart_type)
    else:
        prefix = cfg['prefix'] 
    sec = '{}.'.format(section) if section else ''

    if cfg['use_room_index']:
        apart_num = '{}{}{}.{}'.format(prefix, sec, start_layer, room_index)
        room_num = '{}{}{}.{}.{}'.format(prefix, sec, layer, room_index, r_count)
    else:
        apart_num = '{}{}'.format(sec, start_layer)
        room_num = '{}{}{}.{}'.format(prefix, sec, layer, r_count)

    return apart_num, room_num


#=========================================================
# Применение параметров к помещению
#=========================================================

def apply_room_props(room, 
                     apart_num, 
                     room_num,
                     layer, 
                     room_index, 
                     coef,
                     group, 
                     purpose, 
                     area,
                     gp_code, 
                     section_value,
                     cfg, 
                     live_room):
    """
    
    """

    room.adsk_layer.Set(layer)
    room.adsk_index.Set(room_index)
    room.adsk_coef.Set(coef)

    room.adsk_apart_numb.Set(apart_num)
    room.adsk_room_numb.Set(room_num)

    room.ps_group.Set(group)
    room.ps_purpose.Set(purpose)

    room.adsk_section_str.Set(gp_code)

    if section_value:
        room.ps_section_numb.Set(int(section_value))

    if area is not None:
        room.ps_area_frozen.Set(area)

    if cfg['set_room_count']:
        room.adsk_room_count.Set(live_room)
        if cfg['studio_if_zero'] and live_room == 0:
            room.room_description.Set('Студия')


#=========================================================
# Основная функция
#=========================================================

def create_new_group(doc,
                     rooms,
                     coef_values,
                     ps_groups,
                     ps_purposes,
                     room_index,
                     gp_code,
                     section_value,
                     tr_name=None,
                     set_frozen_area=True,
                     alert=True):
    """
    doc - Ссылка на текущий документ
    rooms - помещения (class RoomItem) сортированные в нужном порядке
    coef_values - значение параметра 'ADSK_Коэффициент площади'
    ps_groups -  значения параметра 'PS_Группа помещения '. Так же важная производная - apart_type
    ps_purposes -  значения параметра 'PS_Назначение_помещения'
    room_index -  значение параметра 'ADSK_Индекс квартиры'
    gp_code -  значение параметра 'ADSK_Номер секции'
    section_value -  значение параметра 'PS_Секция_Число'
    tr_name=None - транзакиця внутри функции или из вне. Если есть имя то будет извне
    set_frozen_area=True - запись замороженной площади
    alert=True - Вывод сообщения 
    """
    apart_type = ps_purposes[0]

    live_room = sum(room.is_living for room in rooms)
    cfg = get_apart_config(apart_type)

    start_layer = get_level(rooms[0])
    messages = []

    def generate(*args):
        r_count = 1
 
        for room, coef, group, purpose in zip(*args):
            layer = get_level(room)

            apart_num, room_num = build_numbers(
                cfg, apart_type, section_value,
                start_layer, layer, room_index, r_count
            )

            apply_room_props(
                room,
                apart_num,
                room_num,
                layer,
                room_index,
                coef,
                group,
                purpose,
                room.rounded_area if set_frozen_area else None,
                gp_code,
                section_value,
                cfg,
                live_room
            )

            messages.append(
                '{}---{}'.format(room.adsk_room_numb.AsString(), room.Name)
            )

            r_count += 1

    if tr_name:
        with Transaction(doc, tr_name) as t:
            t.Start()
            try:
                generate(rooms, coef_values, ps_groups, ps_purposes)
            except Exception:
                print(traceback.format_exc())
            finally:
                t.Commit()
    else:
        try:
            generate(rooms, coef_values, ps_groups, ps_purposes)

        except Exception:
            print(traceback.format_exc())

    if alert:
        forms.alert('Порядок помещений', sub_msg='\n'.join(messages))

    return 'Порядок помещений', messages

#=========================================================
# Получение отсортированных жилых помещений
#=========================================================

def get_sorted_live_rooms(doc, group_by_level=False):
    rooms = FilteredElementCollector(doc) \
        .OfCategory(BuiltInCategory.OST_Rooms) \
        .ToElements()

    rooms = configs.wrap_in_room_item(rooms)
    rooms = [r for r in rooms if r.ps_purpose.AsValueString() == 'Жилье']

    grouped = defaultdict(list)
    for room in rooms:
        grouped[room.adsk_apart_numb.AsValueString()].append(room)

    def sort_key(key):
        return [int(x) for x in key.split('.') if x.isdigit()]

    if not group_by_level:
        return sorted(grouped.items(), key=lambda x: sort_key(x[0]))

    result = defaultdict(list)
    for key, rms in grouped.items():
        level = key.split('.')[1] if '.' in key else '0'
        result[level].append((key, rms))

    for level in result:
        result[level].sort(key=lambda x: sort_key(x[0]))

    return result
