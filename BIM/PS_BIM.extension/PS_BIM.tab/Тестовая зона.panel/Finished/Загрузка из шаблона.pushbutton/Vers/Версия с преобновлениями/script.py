# -*- coding: utf-8 -*-
__title__   = "Обновить\nсемейства"
__doc__ = """Описание: Функция обновления выбранных семейств из шаблона.

Чтобы обновить нужные семейства, вы можете: 

1) Выбрать в проекте нужные вам семейства -> нажать на эту кнопку. В таком случае можно обновить ЛЮБЫЕ семейства, главное, чтобы они были в шаблоне.   
                                ИЛИ
2) Сразу нажать на кнопку. В таком случае возможно обновить только размещенные в проекте семейства, которые начинаются с «PS_» (например, ADKS семейства, так обновить не получится).

Когда вы нажмете на кнопку, на экране появятся пошаговые инструкции. Просто следуйте им.
"""
#==================================================
#IMPORTS
#==================================================

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections
from functions._sketch_plane import set_sketch_plane_to_viewsection
from pyrevit import forms
from pyrevit import revit, DB, UI
from pyrevit.forms import ProgressBar
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button,CheckBox, CommandLink, TaskDialog)

import os
import clr
import re
from collections import defaultdict
clr.AddReference('System.IO')
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
active_view = doc.ActiveView
selection = uidoc.Selection 


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
    # Настройка опций открытия
    deatach_central = DetachFromCentralOption().DoNotDetach

    wokset_config = WorksetConfiguration(WorksetConfigurationOption.OpenAllWorksets)

    options = OpenOptions()
    options.SetOpenWorksetsConfiguration(wokset_config)
    options.DetachFromCentralOption = deatach_central

    # Попытка открыть файл
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
# select = [doc.GetElement(id) for id in uidoc.Selection.GetElementIds() if type(doc.GetElement(id)) is FamilyInstance]
# try:
# sel = [doc.GetElement(id) for id in uidoc.Selection.GetElementIds()]

select = []
for id in uidoc.Selection.GetElementIds():
    if type(doc.GetElement(id)) is FamilyInstance:
        select.append(doc.GetElement(id).LookupParameter("Семейство").AsValueString())
    else:
        try:
            select.append(doc.GetElement(id).Family.Name)
        except:
            pass
        
if select:
    selects_symbol_names = set(select)
    print(selects_symbol_names)
else:
    famly_inst = FilteredElementCollector(doc).OfClass(FamilyInstance).ToElements()
    fe_insts = filter(lambda x: "PS_" in x.LookupParameter("Семейство").AsValueString(), famly_inst)

    # ===== Убрать вложенные семейства =====
    symbols = []
    symbol_cats = []
    symbol_cat_names = []
    names_supcomps = []
    set_symbols = set()
    for symb in fe_insts:
        for subcomp in symb.GetSubComponentIds():
            fam_name = doc.GetElement(subcomp).LookupParameter("Семейство").AsValueString()
            if fam_name not in names_supcomps:
                names_supcomps.append(fam_name)

        name = symb.LookupParameter("Семейство").AsValueString()
        if symb.Name not in set_symbols and name not in names_supcomps:
            symbols.append(symb)
            symbol_cat_names.append(name)
            set_symbols.add(name)
            symbol_cats.append(symb.Category.Name)

    # selects_symbol_names = forms.SelectFromList.show([i.LookupParameter("Семейство").AsValueString() for i in sorted(symbols, key=lambda x:
    #                                                                                         x.LookupParameter("Семейство").AsValueString()[3:])],4
    d = defaultdict(list)
    for k, v in zip(symbol_cats, symbol_cat_names):
        if v not in d[k]:
            d[k].append(v)

    # print(d)
    selects_symbol_names = forms.SelectFromList.show(d,
                title='MultiGroup List',
                group_selector_title='Выберите категорию:',
                multiselect=True,
                button_name='Подтвердить выбор семейств!'
            )
#         selects_symbol_names = forms.SelectFromList.show([i for i in set_symbols],
#                                 multiselect=True,
#                                 button_name='Подтвердить выбор семейств!')
    
if selects_symbol_names:
    # ===== Проверка открытых файлов =====
    to_close = []
    for name in selects_symbol_names:
        if name in open_docs:
            to_close.append(name)

    if not to_close:
        errors = ''
        
        # ===== Форма выббора шаблона =====
        components = [Label('Выберете шаблон для обновления семейства:'),
                    ComboBox('Select_file', {'Шаблон АР/АС': 'Шаблон АР/АС',
                                            'Шаблон КЖ': 'Шаблон КЖ',
                                            'Шаблон КМ':'Шаблон КМ',
                                            'Шаблон Отливы':'Шаблон Отливы'}),
                    # Label('Загрузить с заменой параметров?:'),
                    CheckBox('OverwriteParameter', 'Загрузить без замены параметров?'),
                    Button('Подтвердить выбор')]
        form = FlexForm('Выбор шаблона', components)
        form.show()

        select_file = form.values['Select_file']
        is_OverwriteParameter = form.values['OverwriteParameter']

        # ===== ОТкрытие шабона и посик семейст =====
        file_pasths = {
            'Шаблон АР/АС':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\AR, KR_Шаблон', 
            'Шаблон КЖ':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\KR_Арматура и жб', 
            'Шаблон КМ':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Изделия металлические',
            'Шаблон Отливы':r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Парапеты (отливы+костыли)'
        }

        folder_path = file_pasths[select_file]

        file_to_open = find_latest_rvt_file(folder_path)
        shab_doc = open_model(file_to_open)

        to_copy = []
        shab_famly_symbols = FilteredElementCollector(shab_doc).OfClass(FamilySymbol).ToElements()


        shab_familys_to_load = []
        check = []
        for i in shab_famly_symbols:
            shab_symbol_name = i.FamilyName
            if shab_symbol_name in selects_symbol_names and shab_symbol_name not in check:
                shab_familys_to_load.append(i.Family)
                check.append(shab_symbol_name)

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

        # ===== Открытие семейств и загрузка в проекь =====
        if is_next:
            loaded_fam_name = []
            for family_to_load in shab_familys_to_load:
                doc_family_to_load = shab_doc.EditFamily(family_to_load)
                try:
                    doc_family_to_load.LoadFamily(doc,FamilyLoadOptions())
                    loaded_fam_name.append(family_to_load.Name)
                except Exception as ex:
                    errors = ex
                finally:
                    doc_family_to_load.Close(False)

            # print(len(loaded_fam), len(selects_symbol_names))
            # print(loaded_fam, selects_symbol_names)

            if len(loaded_fam_name) == len(shab_familys_to_load):
                forms.alert('Все семейства загружены:\n\n{}'.format('\n'.join(loaded_fam_name)))
            else:
                diff = set(selects_symbol_names) - set(loaded_fam_name)
                forms.alert('Не удалось загрузить семейства:\n\n{0}\n{1}'.format('\n'.join(diff),errors))

        shab_doc.Close(False)

    else:
        forms.alert("Что бы обновить семейства, закройте файлы:\n{0}".format('\n'.join(to_close)))
else:
    forms.alert('Не выбраны семейства для обновления!')
# except:
#     forms.alert('Выбраны лишние элементы\nВыбирать нужно только семейства!!')


