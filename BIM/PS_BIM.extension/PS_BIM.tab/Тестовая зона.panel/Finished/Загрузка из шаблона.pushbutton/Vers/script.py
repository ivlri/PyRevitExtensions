# -*- coding: utf-8 -*-
__title__   = "Обновить\nсемейства"
__doc__ = """Описание: Функция обновления выбранных семейств из шаблона.

Чтобы обновить нужные семейства, вы можете: 

1) Выбрать в проекте/диспетчере задач нужные вам семейства/типы -> нажать на эту кнопку. Так можно обновить ЛЮБЫЕ семейства, главное, чтобы они были в шаблоне.   
                                ИЛИ
2) Сразу нажать на кнопку. Тогда вам самим придется выбирать семейства для загрузки из тех, что будут найдены в указанном  шаблоне. Если выбранного семейства нет в проекте - оно будет загружено, если уже есть, то семейство будет обновлено.

Когда вы нажмете на кнопку, на экране появятся пошаговые инструкции. Просто следуйте им.
"""
#==================================================
#IMPORTS
#==================================================

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

from pyrevit import forms
from pyrevit import coreutils
from pyrevit.framework import ObservableCollection
from pyrevit.forms import TemplateListItem
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button,CheckBox, CommandLink, TaskDialog)
import sys
import os
import clr
import re
from collections import defaultdict, OrderedDict
clr.AddReference('System.IO')
from pyrevit import script

# import PSForms as forms
output = script.get_output()

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
selection = uidoc.Selection 

# Имена для отображения в окне выбора 
ANNTOTATION_KEYWORDS = ['Марка','Марки', 'Обозначения','Заголовки', 'Обозначение', 'Ссылка на вид', 
                        'Основные надписи', 'Просмотр заголовков', 'Типовые аннотации', "части уровней"]
NAMES_TO_SKIP = ['Граничные условия']
BIM_USERS = ['medvedev', 'chernova.a', 'legostaev']
NOTVERS_TOVERS = False

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
        self.checkall_b.Content = 'Выбрать'
        self.uncheckall_b.Content = 'Отменить'
        self.toggleall_b.Content = 'Обратить'
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


#==================================================
#Classes
#==================================================


class FamilyLoadOptions(IFamilyLoadOptions):
    'Класс для загрузки семейств'


    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        "Поведение при обнаружении семейства в модели"
        global is_OverwriteParameter
        overwriteParameterValues.Value = not is_OverwriteParameter
        return True


    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        "Поведение при обнаружении в модели общего семейства"
        global is_OverwriteParameter
        overwriteParameterValues.Value = True
        if not is_OverwriteParameter:
            source.Value = FamilySource.Family
        else: 
            source.Value = FamilySource.Project
        return True
    

#==================================================
#FUNCTIONS
#==================================================


def find_latest_rvt_file(folder):
    """Находит последний по дате файл с расширением .rvt, исключая резервные копии."""
    rvt_files = []
    
    for file_name in os.listdir(folder):
        if file_name.endswith('.rvt') and not re.search(r'\d{4}$', file_name):
            full_path = os.path.join(folder, file_name)
            file_time = os.path.getmtime(full_path)
            rvt_files.append((full_path, file_time))

    if not rvt_files:
        return None

    latest_file = max(rvt_files, key=lambda x: x[1])
    return latest_file[0]


def open_model(file_copy_path):
    # ===== Настройка опций открытия =====
    deatach_central = DetachFromCentralOption().DoNotDetach

    wokset_config = WorksetConfiguration(WorksetConfigurationOption.OpenAllWorksets)

    options = OpenOptions()
    options.SetOpenWorksetsConfiguration(wokset_config)
    options.DetachFromCentralOption = deatach_central

    # ===== Попытка открыть файл =====
    try:
        ModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_copy_path)
        document = app.OpenDocumentFile(ModelPath, options)

        return document
    
    except Exception as ex:
        return False
    

#==================================================
#MAIN
#==================================================

open_docs = []
for i in app.Documents.ForwardIterator():
    open_docs.append(i.Title.split('.rfa')[0])

# ===== Выбрать семейства для обновления  =====
select = []

for id in uidoc.Selection.GetElementIds():
    try:
        select.append(doc.GetElement(id).LookupParameter("Семейство").AsValueString())
    except:
        select.append(doc.GetElement(id).Family.Name)
    else:
        pass
        
if select:
    selects_symbol_names = set(select)
    is_nt = True
else:
    selects_symbol_names = False
    is_nt = False
    
# ===== Форма выбора шаблона =====
pattern = ['Шаблон КЖ', 'Шаблон КМ', 'Шаблон АР/АС', 'Шаблон Окна/Двери','Шаблон Отливы']
def_patt = {
            'Шаблон КЖ': 'Шаблон КЖ',
            'Шаблон КМ':'Шаблон КМ',
            'Шаблон АР/АС': 'Шаблон АР/АС',
            'Шаблон Окна/Двери':'Шаблон Окна/Двери',
            'Шаблон Отливы':'Шаблон Отливы'
            }

pattern_dict = OrderedDict((key, def_patt[key]) for key in pattern)

components = [Label('Выберите шаблон для обновления семейства:'),
            ComboBox('Select_file', pattern_dict, sort=False),
            CheckBox('OverwriteParameter', 'Загрузка с заменой параметров.', default=True),
            Button('Подтвердить выбор')]
form = FlexForm('Выбор шаблона', components)
form.show()

if form.values:
    select_file = form.values['Select_file']

    is_OverwriteParameter = form.values['OverwriteParameter']

    # ===== ОТкрытие шабона и поиск семейст =====
    file_pasths = {
        'Шаблон АР/АС':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\AR, KR_Шаблон', 
        'Шаблон Окна/Двери':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\AR_Архитектура семейства\Окна и двери', 
        'Шаблон КЖ':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\KR_Арматура и жб', 
        'Шаблон КМ':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Изделия металлические',
        'Шаблон Отливы':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Парапеты (отливы+костыли)'
    }

    folder_path = file_pasths[select_file]

    file_to_open = find_latest_rvt_file(folder_path)

    # doc_famly = FilteredElementCollector(doc).OfClass(ElementType).ToElements()
    # for i in doc_famly:
    #     print(i)
    shab_doc = open_model(file_to_open)

    # ===== Поиск всех семейств в открытом документе + фильтрация + версия
    doc_famly = FilteredElementCollector(doc).OfClass(Family).ToElements()
    
    doc_name_family_dict = {
            fam.Name: fam
            for fam in doc_famly
        }

    sdoc_filtered_families = [
            fam for name, fam in doc_name_family_dict.items() 
            if name and ("PS_" in name or "ADSK_" in name)
        ]
    
    doc_famly_values = {
            fam.Name: doc.GetElement(list(fam.GetFamilySymbolIds())[0]).LookupParameter("ADSK_Версия семейства")
            for fam in sdoc_filtered_families
        }

    # ===== Поиск всех семейств в шаблоне + фильтрация + версия
    shab_famly = FilteredElementCollector(shab_doc).OfClass(Family).ToElements()
    
    param_values = {
            fam: fam.Name
            for fam in shab_famly
        }

    shab_filtered_families = [
            fam for fam, value in param_values.items() 
            if value and ("PS_" in value or "ADSK_" in value)
        ]
    
    shab_famly_values = {
            fam.Name: shab_doc.GetElement(list(fam.GetFamilySymbolIds())[0]).LookupParameter("ADSK_Версия семейства")
            for fam in shab_filtered_families
        }
    
    # ===== Список всех родительских и вложеных вложеных семейств 
    famly_insts = FilteredElementCollector(shab_doc).OfClass(FamilyInstance).ToElements()

    filtered_families_inst = []
    for famly_inst in famly_insts:
        family = famly_inst.LookupParameter("Семейство").AsValueString()
        if any(pref in family for pref in ['PS_', 'ADSK_']):
            filtered_families_inst.append(famly_inst)
        
    names_supcomps = []
    for symb in filtered_families_inst:
        for subcomp in symb.GetSubComponentIds():
            fn = shab_doc.GetElement(subcomp).LookupParameter("Семейство").AsValueString()
            if fn not in names_supcomps:
                names_supcomps.append(fn)
    
    #===== Сбора всех семейсвт проекта(без вложеных) 
    if not selects_symbol_names: # Ветка без предварительного выбора
        familys_to_load = []
        names_familys_toload = []
        cattegorus_familys_toload = []
        version_family = []
        is_bim = []
        for i in shab_filtered_families:
            shab_fam_name = i.Name
            if shab_fam_name not in names_familys_toload and shab_fam_name not in names_supcomps:
                cat_name = i.FamilyCategory.Name
                if any(to_skip not in cat_name for to_skip in NAMES_TO_SKIP):
                    if any(keyword in cat_name for keyword in ANNTOTATION_KEYWORDS):
                        cattegorus_familys_toload.append('Аннотации')
                    else:
                        cattegorus_familys_toload.append(cat_name)

                    names_familys_toload.append(shab_fam_name)
                    familys_to_load.append(i)

                    #Определение версии семейства в файле
                    # print(shab_fam_name)
                    # print(doc_famly_values[shab_fam_name])
                    try:
                        doc_vers_fam = doc_famly_values[shab_fam_name].AsValueString()
                        doc_v_out = 'v{} -> '.format(doc_vers_fam)
                    except:
                        doc_vers_fam = ''
                        doc_v_out = ''

                    try:
                        shab_vers_fam = shab_famly_values[shab_fam_name].AsValueString()
                        shab_version_out = 'v{}'.format(shab_vers_fam)
                    except:
                        shab_vers_fam = ''
                        shab_version_out = ''

                    if (doc_vers_fam.split('.')[0] < shab_vers_fam.split('.')[0]) and doc_v_out and shab_version_out:
                        version_family.append('     {0}{1} (BIM)'.format(doc_v_out, shab_version_out))
                        is_bim.append(shab_fam_name)

                    elif (doc_vers_fam.split('.')[0] > shab_vers_fam.split('.')[0]) and doc_v_out and shab_version_out:
                        version_family.append('     {0}{1} ОШИБКА!!!'.format(doc_v_out, shab_version_out))
                        # print('1) {}'.format(shab_fam_name))
                        is_bim.append(shab_fam_name)

                    elif (not doc_v_out and shab_version_out): # в файле нет версии а в шаблоне есть
                        version_family.append('     v... -> {} (BIM)'.format(shab_version_out))

                    else: # Версии нет и в шаблоне и в файле
                        version_family.append('     {0}{1}'.format(doc_v_out, shab_version_out))
                    # elif ('.'.join(doc_vers_fam.split('.')[:2]) != '.'.join(shab_vers_fam.split('.')[:2]) and doc_v_out and shab_version_out):
                    #     version_family.append('     {0} -> {1}'.format(doc_v_out, shab_version_out))
                    #     # print('2) {}'.format(shab_fam_name))

                    # else: # Версии нет и в шаблоне и в файле
                    #     version_family.append('     ')
                    #     # print('3) {}'.format(shab_fam_name)) 
                    
                        
        # ===== Сборка правильного словаря для вывода
        dict_names_to_select = defaultdict(list)
        for key, value, vers in zip(cattegorus_familys_toload, names_familys_toload, version_family):
            if value not in dict_names_to_select[key]:
                dict_names_to_select[key].append(value + vers)

        dict_name_file = defaultdict(list)
        for family, name in zip(familys_to_load, names_familys_toload):
            dict_name_file[name].append(family)  # Ключ - имя семейства, значение - список семейств

        # output.print_md("## Список семейств в проекте")
        # for family_name, family_objects in dict_name_file.items():
        #     output.print_md("**{}:{}**".format(family_name, family_objects[0].Name))
        #     # print(family_objects)

        sorted_dict = defaultdict(list)
        for key in sorted(dict_names_to_select):
            sorted_dict[key] = sorted(dict_names_to_select[key], key=lambda x: x.split('     ')[0])\
            
        #===== Ставим Обобщенные модели на первое место
        lest_keys = list(sorted_dict.keys())
        lest_keys.pop(lest_keys.index('Обобщенные модели'))
        new_sort = ['Обобщенные модели'] 
        new_sort.extend(sorted(lest_keys))

        new_dict = OrderedDict((key, sorted_dict[key]) for key in new_sort)

        # ===== Вывод окна =====
        selects_symbol_names = forms.SelectFromList.show(new_dict,
                    title='Выбор семейств для загрузки',
                    group_selector_title='Выберите категорию:',
                    multiselect=True,
                    button_name='Подтвердить выбор семейств!',
                )
        
        shab_familys_to_load = []
        if selects_symbol_names:
            selects_symbol_names = [i.split('     ')[0] for i in selects_symbol_names]
            diff = any(i for i in is_bim if i in selects_symbol_names) # определение наличия запрещенки

            if diff:
                paswor = forms.ask_for_string(
                        prompt='Некоторые выбранные элементы запрещено обновлять!',
                        title='Запрет обновления: ВВЕДИТЕ ПАРОЛЬ'
                        )
                if paswor != '0000':
                    shab_doc.Close(False)
                    forms.alert('Пароль не правильный')
                    sys.exit()

            shab_familys_to_load = [dict_name_file[i] for i in selects_symbol_names]
            shab_familys_to_load = sum(shab_familys_to_load, [])
            is_next = True
        else:
            forms.alert('Не выбраны семейства для обновления!')

    #-------------------------------------------------------------------------------
    else:# Ветка с предварительным выбором
        shab_familys_to_load = []
        check = []
        start_vers_fam = []
        is_bim = False

        for i in shab_famly:
            shab_fam_name = i.Name
            if shab_fam_name in selects_symbol_names and shab_fam_name not in check:
                shab_familys_to_load.append(i)
                check.append(shab_fam_name)

                #Версия семейства в проекте 
                fam_in_doc = doc_name_family_dict[shab_fam_name]
                doc_symbol = doc.GetElement(list(fam_in_doc.GetFamilySymbolIds())[0])
                try:
                    doc_vers_fam = doc_symbol.LookupParameter("ADSK_Версия семейства").AsValueString()
                    start_vers_fam.append(doc_vers_fam)
                except:
                    doc_vers_fam = ''

                try:
                    end_vers_fam = shab_famly_values[shab_fam_name].AsValueString()
                except:
                    doc_vers_fam = ''

                if doc_vers_fam.split('.')[0] != end_vers_fam.split('.')[0]:
                    is_bim = True

        if is_bim:
            paswor = forms.ask_for_string(
                    prompt='Некоторые выбранные элементы запрещено обновлять!',
                    title='Запрет обновления: ВВЕДИТЕ ПАРОЛЬ'
                    )
            if paswor != '0000':
                shab_doc.Close(False)
                sys.exit()

        # ===== Обработка семейств какторые небыли найдены в шаблоне =====
        diff = set(selects_symbol_names) - set(check) 
        is_next = True
        if diff: 
            commands= [CommandLink('Пропусить данные семейства и обновить остальные', return_value=True),
            CommandLink('Завершить операцию', return_value=False)]
            dialog = TaskDialog('{0} из {1} выбранных семейств не найдены в {2}. Возможно выбран не правильный шаблон или не совпали имена семейств:\n\n{3}'.format(len(diff),
                                                                                                                                                                    len(selects_symbol_names),
                                                                                                                                                                    select_file,
                                                                                                                                                                    '\n'.join(diff)),
                                title_prefix=False,
                                content="Выберите дальнейшее действие!",
                                commands=commands,
                                show_close=True)

            is_next = dialog.show()
            shab_familys_to_load = set(shab_familys_to_load) - diff

        shab_familys_to_load = [i for i in shab_familys_to_load]
    to_close = []
    errors = ''
    # ===== Проверка открытых семейств =====
    try:
        for name in selects_symbol_names:
            if name in open_docs:
                to_close.append(name)
        if not to_close:
            # ===== Открытие семейств и загрузка в проект =====
            if is_next:
                loaded_fam_name = []
                not_loaded_fam_name = []
                # flatt_fam_toload = sum(shab_familys_to_load, [])
                for family_to_load in shab_familys_to_load:
                    #----- Загрузка семейств -----
                    doc_family_to_load = shab_doc.EditFamily(family_to_load)
                    try:
                        doc_family_to_load.LoadFamily(doc,FamilyLoadOptions())
                        loaded_fam_name.append(family_to_load.Name)
                    except Exception as ex:
                        forms.alert(ex)
                    finally:
                        doc_family_to_load.Close(False)

                if len(loaded_fam_name) == len(shab_familys_to_load):
                    forms.alert('Cемейства загружены:\n\n{}'.format('\n'.join(loaded_fam_name)))
                else:
                    diff = set(selects_symbol_names) - set(loaded_fam_name)
                    forms.alert('Не удалось загрузить некоторые семейства:\n\n{0}\n{1}'.format('\n'.join(diff),errors))

            shab_doc.Close(False)

        else:
            forms.alert("Чтобы обновить семейства, закройте файлы:\n{0}".format('\n'.join(to_close)))
    except TypeError:
        pass
