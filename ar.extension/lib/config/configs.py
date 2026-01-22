# -*- coding: utf-8 -*-
import json
import os
import codecs
import os
import pickle
import traceback
from tempfile import gettempdir

# -*- coding: utf-8 -*-
from pyrevit import forms
from pyrevit import coreutils
from pyrevit.framework import ObservableCollection
from pyrevit.forms import TemplateListItem


class RoomItem:
    LIVING_NAMES = ['Спальня', 'Кабинет', 'Жилая комната', 'Гостиная']
    STUD = ['Гостиная']
    COEF = 10.76391041670966

    def __init__(self,room):
        self.element = room
        self.id = room.Id

        self.adsk_layer = room.LookupParameter('ADSK_Этаж')
        self.adsk_index = room.LookupParameter('ADSK_Индекс квартиры')
        self.adsk_room_count = room.LookupParameter('ADSK_Количество комнат')
        self.adsk_coef = room.LookupParameter('ADSK_Коэффициент площади')
        self.adsk_apart_numb = room.LookupParameter('ADSK_Номер квартиры')
        self.adsk_room_numb = room.LookupParameter('ADSK_Номер помещения квартиры')
        self.adsk_section_str = room.LookupParameter('ADSK_Номер секции')
        self.adsk_area_with_coef = room.LookupParameter('ADSK_Площадь с коэффициентом')
        self.adsk_apart_type = room.LookupParameter('ADSK_Тип квартиры')
        self.adsk_area = room.LookupParameter('ADSK_Площадь квартиры')
        self.adsk_area_live = room.LookupParameter('ADSK_Площадь квартиры жилая')
        self.adsk_numb_in_home = room.LookupParameter('ADSK_Номер квартиры в доме')

        self.ps_area_without_coef = room.LookupParameter('PS_Площадь квартиры без коэффициента ')
        self.ps_group = room.LookupParameter('PS_Группа помещения ')
        self.ps_purpose = room.LookupParameter('PS_Назначение_помещения')
        self.ps_area_frozen = room.LookupParameter('PS_Площадь помещения (замороженная)')
        self.ps_area_frozen_coef = room.LookupParameter('PS_Площадь помещения (замороженная) с коэффициентом')
        self.ps_area_summer = room.LookupParameter('PS_Площадь летних  ')
        self.ps_section_numb = room.LookupParameter('PS_Секция_Число')
        self.room_description = room.LookupParameter('PS_Описание помещения')

    @property
    def Name(self):
        return self.element.LookupParameter('Имя').AsValueString()
    
    @property
    def Area(self):
        return self.element.LookupParameter('Площадь').AsDouble()
    
    @property
    def LevelName(self):
        return self.element.LookupParameter('Уровень').AsValueString()
    
    @property
    def is_living(self):
        return self.Name in self.LIVING_NAMES
    
    @property
    def rounded_area(self):
        area = self.Area / self.COEF
        return round(area, 1) * self.COEF
    
    @classmethod
    def round_area(self, area):
        area = area / self.COEF
        return round(area, 1) * self.COEF
    
def get_context():
    doc   = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument
    app   = __revit__.Application
    return doc, uidoc, app

def get_groups():
    file_path = os.path.join(os.path.dirname(__file__), 'rooms_groups.json')
    with codecs.open(file_path, 'r', encoding='utf-8') as f:
        rooms_groups = json.load(f)
    return rooms_groups

def wrap_in_room_item(data_list):
    return [RoomItem(i) for i in data_list]

def rb_temp(value=None):
    tempfile = os.path.join(gettempdir(), 'Using alert')

    if not os.path.exists(tempfile):
        with open(tempfile, 'wb') as fp:
            pickle.dump(True, fp)
    

    # ---------- ЧТЕНИЕ ----------
    if value is None:
        with open(tempfile, 'rb') as fp:
            return pickle.load(fp)

    # ---------- ЗАПИСЬ ----------
    with open(tempfile, 'wb') as fp:
        pickle.dump(value, fp)


    return value


#==============================================================
#Customization SelectFromList to return all values in a groups
#==============================================================

def _prepare_context(self):
        if isinstance(self._context, dict) and self._context.keys():
            self._update_ctx_groups(self._context.keys())
            new_ctx = {}
            for ctx_grp, ctx_items in self._context.items():
                new_ctx[ctx_grp] = self._prepare_context_items(ctx_items)
            self._context = new_ctx
        else:
            self._context = self._prepare_context_items(self._context)

forms.SelectFromList._prepare_context = _prepare_context

def _list_options(self, option_filter=None):
    if option_filter:
        self.checkall_b.Content = 'Выбрать все'
        self.uncheckall_b.Content = 'Отменить все'
        self.toggleall_b.Content = 'Обратить все'
        # Get all items from all groups if context is a dict
        if isinstance(self._context, dict):
            self.all_items = [item for group in self._context.values() for item in group]
        else:
            self.all_items = self._context
        # get a match score for every item and sort high to low
        fuzzy_matches = sorted(
            [(x,
                coreutils.fuzzy_search_ratio(
                    target_string=x.name,
                    sfilter=option_filter,
                    regex=self.use_regex))
                for x in self.all_items],
            key=lambda x: x[1],
            reverse=True
            )
        # filter out any match with score less than 80
        self.list_lb.ItemsSource = \
            ObservableCollection[TemplateListItem](
                [x[0] for x in fuzzy_matches if x[1] >= 80]
                )
    else:
        self.checkall_b.Content = 'Выбрать все'
        self.uncheckall_b.Content = 'Отменить все'
        self.toggleall_b.Content = 'Обратить все'
        self.list_lb.ItemsSource = \
            ObservableCollection[TemplateListItem](self._get_active_ctx())

forms.SelectFromList._list_options = _list_options

def _get_options(self):
    if self.multiselect:
        if self.return_all:
            return [x for x in self._get_active_ctx()]
        else:
            selected_items = []
            if isinstance(self._context, dict):
                for group_items in self._context.values():
                    selected_items.extend(
                        item for item in group_items
                        if item.state or item in self.list_lb.SelectedItems
                    )
            else:
                selected_items.extend(
                    item for item in self._context
                    if item.state or item in self.list_lb.SelectedItems
                )
            return self._unwrap_options(selected_items)
    else:
        return self._unwrap_options([self.list_lb.SelectedItem])[0]

forms.SelectFromList._get_options = _get_options