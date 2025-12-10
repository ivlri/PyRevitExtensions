# -*- coding: utf-8 -*-
__title__   = "Копирайтер"
__doc__ = """Описание: Функция для переноса параметров экземпляра между элементами.

Чтобы перенести параметры нужно:
1) Выбрать семейство, чьи параметры нужно перенести
2) Нажать на кнопку -> в появившемся окне выбрать пункт - "Сохранить параметры"
3) Выбрать семейство, куда нужно перенести параметры -> нажать на кнопку -> в появившемся окне выбрать пункт - "Переписать параметры"
"""
__highlight__ = "new"
#==================================================
#IMPORTS
#==================================================
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Collections.Generic import List
import json
import codecs

import sys
import os
import clr
clr.AddReference('System.IO')
from pyrevit import script
from pyrevit import forms
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button,CheckBox, CommandLink, TaskDialog)

from pyrevit.framework import ObservableCollection
from pyrevit.forms import TemplateListItem
from pyrevit import coreutils
from System import Double


#==============================================================
#Customization SelectFromList
#==============================================================


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


def _prepare_context_items(self, ctx_items):
    new_ctx = []
    # filter context if necessary
    if self.filter_func:
        ctx_items = filter(self.filter_func, ctx_items)

    for item in ctx_items:
        if isinstance(item, TemplateListItem):
            item.checkable = self.multiselect
            if self.multiselect:
                item.checked = True 
            new_ctx.append(item)
        else:
            new_item = TemplateListItem(
                item,
                checkable=self.multiselect,
                name_attr=self._nameattr
            )
            if self.multiselect:
                if not any(i in new_item.name for i in NOTACTIVE_PARAMETERS):
                    new_item.checked = True
                else:
                    new_item.checked = False
            new_ctx.append(new_item)

    return new_ctx


forms.SelectFromList._prepare_context_items = _prepare_context_items


def _get_options(self):
    if self.multiselect:
        if self.return_all:
            return [x for x in self._get_active_ctx()]
        else:
            return self._unwrap_options(
                [x for x in self._get_active_ctx() if x.state] 
                )
    else:
        return self._unwrap_options([self.list_lb.SelectedItem])[0]

forms.SelectFromList._get_options = _get_options

#==================================================
#MAIN
#==================================================

FILTERED_PARAMETERS = [
    "PS_Секция_",
    'PS_Номер этажа_Число',
    "Номер секции",
    "ADSK_Этаж",
    "ADSK_Зона",
    "ADSK_Группирование",
    "ADSK_Позиция",
    "ADSK_Примечание"
]

NOTACTIVE_PARAMETERS = ["ADSK_Марка", "ADSK_Метка основы", "ADSK_Категория основы", "ADSK_Отверстие_Отметка", "PS_Вложение (вкл/выкл)","PS_Тип вложения"]

output = script.get_output()

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
selection = uidoc.Selection 

js_file_dir = os.path.dirname(__file__) + "\{}_params.json".format(app.Username)
doc_title = doc.Title

selected_elements = [doc.GetElement(id) for id in uidoc.Selection.GetElementIds()]

#===== Проверки выбора =====
for i in selected_elements:
    if not isinstance(i,FamilyInstance):
        forms.alert(msg='Выбран посторонний элемент.',sub_msg='Выберете только размещенные в проекте семейства и повторите попытку.')
        sys.exit()

if len(selected_elements) == 0:
    forms.alert('Не выбрано семейство.')
    sys.exit()

#===== Выбор режима работы =====  
commands= [CommandLink('1. Сохранить параметры.', return_value='save'),
           CommandLink('2. Перенести параметры', return_value='set')
           ]
dialog = TaskDialog('Выберите режим работы!',
                    title_prefix=False,
                    title="Копирайтер",
                    commands=commands,
                    show_close=True
                    )
mode = dialog.show()

#===== Режим сохранения =====
if mode == "save":
    if len(selected_elements) > 1:
        forms.alert('Выбрано несколько элементов.', sub_msg="Для сохранения параметров выберете только один элемент и попробуйте снова.")
        sys.exit()
    try:
        out_dir = {}
        #----- Отсев лишнего -----
        for param in selected_elements[0].Parameters:
            param_value = param.AsValueString()
            if 'autodesk.revit.parameter' not in param.GetTypeId().TypeId and not param.IsReadOnly and param_value is not None and param_value and param.HasValue:
                par_name = param.Definition.Name
                if param_value == "(нет)" or any(i in par_name for i in FILTERED_PARAMETERS):
                    continue

                out_dir[par_name] = param_value
                
        paramname_to_save = [par for par,_ in out_dir.items()]
        paramname_to_save = forms.SelectFromList.show(sorted(paramname_to_save),
                        title='Сохранить параметры',
                        multiselect=True,
                        button_name='Подтвердить выбор!'
                    )
        params_to_save = {}
        if paramname_to_save:          
            params_to_save = {
                par:val
                for par,val in out_dir.items() if par in paramname_to_save
            } 

            selected_type_name = selected_elements[0].LookupParameter("Тип").AsValueString()
            params_to_save['type_name'] = selected_type_name
            params_to_save['fam_name'] = selected_elements[0].LookupParameter("Семейство").AsValueString()
            params_to_save['doc_title'] = doc.Title

            lst = [params_to_save]
            with codecs.open(js_file_dir,'w',encoding='utf-8') as f:
                json.dump(params_to_save, f,ensure_ascii=False,indent=4)

            forms.alert("Параметры для типа '{}' были сохранены.".format(selected_type_name))
        else:
            forms.alert("Небыли выбраны параметры для сохранения!")
            sys.exit()
    except Exception as ex:
        forms.alert(str(ex))

#===== Режим записи =====
if mode == 'set':
    with codecs.open(js_file_dir, 'r', encoding='utf-8') as f:
        js_data = json.load(f)

    #----- Проверка на правильность семейства -----
    selected_type_names = []
    for selected_element in selected_elements:
        selected_type_name = selected_element.LookupParameter("Тип").AsValueString()
        selected_fam_name = selected_element.LookupParameter("Семейство").AsValueString()
        selected_type_names.append(selected_type_name)

        if selected_fam_name != js_data['fam_name']:
            forms.alert(msg="Замена невозможна.", title="Копирайтер", 
                        sub_msg='Параметры записаны для семейства "{}", а выбрано семейство "{}"'.format(js_data['fam_name'], selected_fam_name),
                        footer='')
            sys.exit()

    #----- Предупреждение о разных типах -----
    if any(js_data['type_name'] != selected_type_name for selected_type_name in selected_type_names):
        commands = [CommandLink('Продолжить замену параметров', return_value=True),
        CommandLink('Завершить процесс', return_value=False)]
    
        dialog = TaskDialog('Попытка заменить параметры экземпляра в другом типе',
                            title_prefix=False,
                            title="Копирайтер",
                            content='Параметры экземпляра сохранены для типа: \n"{}"\nВыбранные типы: \n{}'.format(js_data['type_name'],'\n'.join(selected_type_names)),
                            commands=commands,
                            show_close=True)
        is_next = dialog.show()
    
    #----- Цикл записи -----
    is_next = True
    for selected_element in selected_elements:
        selected_type_name = selected_element.LookupParameter("Тип").AsValueString()
        selected_fam_name = selected_element.LookupParameter("Семейство").AsValueString()

        error_param = []
        if is_next:
            with Transaction(doc, 'Перенос параметров') as t:
                t.Start()
                for set_param, set_value in js_data.items():
                    if set_param in ['doc_title', 'type_name', "fam_name"]:
                        continue
                    if set_value == '' or set_value is None:
                        continue
                    if set_value == 'Да': 
                        set_value = 1
                    if set_value == "Нет":
                        set_value = 0
                    
                    param_to_set = selected_element.LookupParameter(set_param)
                    if param_to_set is None:
                        error_param.append(set_param)
                        continue
                    else:
                        param_stype = param_to_set.StorageType
                        
                        #----- Обработка различных типов данных -----
                        if param_stype == StorageType.ElementId and param_to_set is not None:
                            """
                            Сперва идет попытка сплита. Если удачна, то это параметр с выбором семейства. 

                            В первую очередь идет поиск "классического" семейства для вставки в параметр. Если не найден, 
                            то попытка найти особое семейство антуража.
                            """
                            txt_split = set_value.split(' : ')

                            if len(txt_split) > 1:
                                family, family_type = txt_split
                                doc_families = FilteredElementCollector(doc).OfClass(Family).ToElements()

                                fe_fam = filter(lambda x: x.Name == family, doc_families)
                                if fe_fam:
                                    fe_fam_symbols = list(fe_fam[0].GetFamilySymbolIds())
                                    fe_set_value = filter(lambda x: doc.GetElement(x).LookupParameter("Имя типа").AsValueString() == family_type, 
                                                          fe_fam_symbols
                                                          )
                                    
                                    set_value = fe_set_value[0]
                                else: # Поиск семейства антуража
                                    element_ordered_parameters = selected_element.Symbol.GetOrderedParameters()
                                    type_to_set = [i.AsElementId() for i in element_ordered_parameters if i.AsValueString() == set_value]
                                    if type_to_set:
                                        set_value = type_to_set[0]
                                    else:
                                        forms.alert(msg='Не найдено семейство "{}" или его тип "{}", который должен быть указан в параметре {}'.format(family,family_type,set_param),
                                                    sub_msg='Проверьте наличие дублей и сохраните параметры заново')
                                        sys.exit()
                            else: # Обработка материалов
                                if set_value == "<По категории>":
                                    set_value = ElementId(-1)
                                else:
                                    materials_id = FilteredElementCollector(doc).OfClass(Material).ToElementIds()
                                    fe_materials = filter(lambda x: doc.GetElement(x).Name == set_value, materials_id)
                                    set_value = fe_materials[0]
                        
                        if param_stype == StorageType.Double: # Double - Особенные, им нужен другой метод
                            param_to_set.SetValueString(set_value)
                            continue
                        if param_stype == StorageType.Integer:
                            set_value = int(set_value)

                        param_to_set.Set(set_value)
                t.Commit()

        else:
            sys.exit()

    if error_param:
        forms.alert(msg='Параметры заменены частично',sub_msg='Указанные ниже параметры, что были найдены в {}, не были найдены в целевом проекте - {}. Передайте данную информацию BIM-отдел.\n\n{}'.format(js_data['doc_title'],doc.Title,'\n'.join(error_param)))
