# -*- coding: utf-8 -*-
from itertools import count

from rpw.utils.dotnet import Enum
from rpw.ui.forms.resources import *
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Collections.Generic import List
import re
from pyrevit import HOST_APP, EXEC_PARAMS, DOCS, BIN_DIR
from pyrevit import revit, UI, DB, script

import time

from pyrevit import coreutils
from pyrevit import versionmgr
from pyrevit.framework import ObservableCollection
from pyrevit.forms import TemplateListItem
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox,
                          Separator, Button,CheckBox, CommandLink, TaskDialog)
import sys
import os
import clr
import re
from collections import defaultdict, OrderedDict
clr.AddReference('System.IO')
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, DialogResult
from pyrevit import revit, forms, script
from Autodesk.Revit import DB
from System.Collections.Generic import List
from pyrevit.coreutils.logger import get_logger
from Autodesk.Revit.DB import FilteredElementCollector, ViewFamilyType, ElementId, ViewFamily, Transaction
from Autodesk.Revit.DB import Element

# Добавляем логирование использования инструмента
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()


logger = script.get_logger()
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
selection = uidoc.Selection 

# Проверка и создание типа вида проверочного
def create_3d_view_type(name):
    collector = FilteredElementCollector(doc).OfClass(ViewFamilyType).WhereElementIsElementType()
    
    # Добавлено: проверка существующего типа
    existing_type = next((vft for vft in collector if Element.Name.__get__(vft) == name), None)
    if existing_type:
        return existing_type.Id
    
    base_type = None
    for vft in collector:
        if vft.ViewFamily == ViewFamily.ThreeDimensional and vft.DefaultTemplateId == ElementId.InvalidElementId:
            base_type = vft
            break

    try:
        t = Transaction(doc, "PS Создание типа 3D видов")
        t.Start()
        new_type = base_type.Duplicate(name)
        t.Commit()   
        return new_type.Id
            
    except Exception as e:
        if t.HasStarted():
            t.RollBack()
       
        return None
        
created_type_id = create_3d_view_type("PS_Визуальные проверки")




# --- Выбор последней версии файла ---
def find_latest_rvt_file(folder):
    """Находит последний по дате файл с расширением .rvt, исключая резервные копии."""
    rvt_files = []

    for file_name in os.listdir(folder):
        if file_name.endswith('.rvt') and not re.search(r'\.\d{4}$', file_name):  # исключаем резервные копии вида .0001.rvt
            full_path = os.path.join(folder, file_name)
            file_time = os.path.getmtime(full_path)
            rvt_files.append((full_path, file_time))

    if not rvt_files:
        return None

    latest_file = max(rvt_files, key=lambda x: x[1])
    return latest_file[0]



# --- Выбор файла шаблона через UI ---

if "_AR_" in doc.Title:
    pattern = ['Шаблон АР/КР', 'Шаблон КЖ', 'Шаблон КМ']
else:
    pattern = ['Шаблон КЖ','Шаблон АР/КР', 'Шаблон КМ']

def_patt = {
    'Шаблон КЖ': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\KR_Арматура и жб',
    'Шаблон КМ': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Изделия металлические',
    'Шаблон АР/КР': r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\AR, KR_Шаблон',
}

pattern_dict = OrderedDict((key, def_patt[key]) for key in pattern)

components = [
    Label('Выберите шаблон для загрузки шаблонов вида:'),
    ComboBox('Select_file', pattern_dict, sort=False),
    Button('Подтвердить выбор')
]

form = FlexForm('Выбор файла шаблона', components)
form.show()

if not form.values or not form.values.get('Select_file'):
    forms.alert("Операция отменена пользователем.", title="Отмена")
    raise SystemExit()

selected_folder_or_file = form.values['Select_file']

if os.path.isdir(selected_folder_or_file):
    template_path = find_latest_rvt_file(selected_folder_or_file)
    if not template_path:
        forms.alert("В папке не найдено подходящих файлов .rvt", title="Ошибка")
        raise SystemExit()
else:
    template_path = selected_folder_or_file



if not os.path.exists(template_path):
    forms.alert("Файл шаблона не найден:\n{}".format(template_path), title="Ошибка")
    raise SystemExit()

# --- Открываем выбранный файл шаблона ---
model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(template_path)
open_opts = DB.OpenOptions()
open_opts.DetachFromCentralOption = DB.DetachFromCentralOption.DoNotDetach
source_doc = doc.Application.OpenDocumentFile(model_path, open_opts)

# Получаем все шаблоны видов с "PS" в имени
all_views = DB.FilteredElementCollector(source_doc).OfClass(DB.View).WhereElementIsNotElementType().ToElements()
view_templates = [v for v in all_views if v.IsTemplate and "PS" in v.Name]

# Группируем по правилам
grouped_templates = defaultdict(list)
for v in view_templates:
    name = v.Name
    if "роверка" in name:
        grouped_templates["1. Проверочные"].append(v)
    else:
        grouped_templates["2. Оформление"].append(v)

# Группа "Все" — все шаблоны с "PS"
grouped_templates["3. Все"] = view_templates

# Сортируем внутри групп по имени
for group in grouped_templates:
    grouped_templates[group] = sorted(grouped_templates[group], key=lambda x: x.Name)

# Упорядочиваем группы с нужным порядком
ordered_groups = ["1. Проверочные", "2. Оформление", "3. Все"]
ordered_grouped_templates = OrderedDict((grp, grouped_templates.get(grp, [])) for grp in ordered_groups)


# Проверка, что есть что выбирать
if all(len(v) == 0 for v in ordered_grouped_templates.values()):
    forms.alert("В шаблонном файле нет подходящих шаблонов видов.", title="Информация")
    source_doc.Close(False)
    raise SystemExit()



class MySelectFromList(forms.SelectFromList):
    def _list_options(self, option_filter=None):
        # Сначала вызываем базовый метод, чтобы всё корректно инициализировалось
        super(MySelectFromList, self)._list_options(option_filter)
        # Потом меняем подписи кнопок
        self.checkall_b.Content = 'Выбрать все'
        self.uncheckall_b.Content = 'Отменить все'
        self.toggleall_b.Content = 'Обратить все'


selected_templates = MySelectFromList.show(
    ordered_grouped_templates,
    name_attr="Name",
    title="Выберите шаблоны вида для копирования",
    group_selector_title="Выберите группу:",
    multiselect=True,
    button_name='Подтвердить выбор!'
)



if not selected_templates:
    source_doc.Close(False)
    forms.alert("Ничего не выбрано. Операция отменена.", title="Отмена")
    raise SystemExit()

# Получаем текущие шаблоны в активном документе
current_templates = {
    v.Name: v for v in DB.FilteredElementCollector(doc)
    .OfClass(DB.View)
    .WhereElementIsNotElementType()
    .ToElements()
    if v.IsTemplate
}

with DB.Transaction(doc, "PS Копирование шаблонов видов из файла-шаблона") as tr:
    tr.Start()
    
    operation_cancelled = False
    for template in selected_templates:
        name = template.Name
        template_id = template.Id

        if name in current_templates:
            # Вместо стандартного MessageBox.Show(...) вот это:
          


            commands = [
                CommandLink('Пропустить и продолжить', return_value='skip'),
                CommandLink('Заменить шаблон', return_value='replace'),
                CommandLink('Создать копию (с цифрой)', return_value='copy'),
                
                #CommandLink('Отменить операцию', return_value='cancel')
            ]

            dialog = TaskDialog(
                "Шаблон '{}' уже существует.".format(name),  # content — первый позиционный аргумент
                title='Конфликт шаблонов',
                title_prefix=False,
                content="Внимание! Правила фильтров остаются из текущего проекта.\n\nВыберите дальнейшее действие: ",
                commands=commands,
                #buttons=['Cancel'],
                show_close=True
            )

            user_choice = dialog.show()

            if user_choice == 'skip':
                continue

            
            if user_choice == None:
                operation_cancelled = True
                break


            if user_choice == 'replace':
                old_template = current_templates[name]

                # Найти все виды, использующие этот шаблон
                dependent_views = [
                    v for v in DB.FilteredElementCollector(doc)
                    .OfClass(DB.View)
                    .WhereElementIsNotElementType()
                    .ToElements()
                    if not v.IsTemplate and v.ViewTemplateId == old_template.Id
                ]

                # Удалить старый шаблон
                doc.Delete(old_template.Id)

                # Скопировать новый
                class ReplaceHandler(DB.IDuplicateTypeNamesHandler):
                    def OnDuplicateTypeNamesFound(self, args):
                        return DB.DuplicateTypeAction.UseDestinationTypes

                options = DB.CopyPasteOptions()
                options.SetDuplicateTypeNamesHandler(ReplaceHandler())

                copied_ids = DB.ElementTransformUtils.CopyElements(
                    source_doc,
                    List[DB.ElementId]([template_id]),
                    doc,
                    None,
                    options
                )

                new_template_id = copied_ids[0]

                # Назначить новый шаблон обратно на виды
                for v in dependent_views:
                    v.ViewTemplateId = new_template_id

            elif user_choice == 'copy':
                # Копируем шаблон с созданием копий
                class CopyHandler(DB.IDuplicateTypeNamesHandler):
                    def OnDuplicateTypeNamesFound(self, args):
                        return DB.DuplicateTypeAction.UseDestinationTypes

                options = DB.CopyPasteOptions()
                options.SetDuplicateTypeNamesHandler(CopyHandler())

                DB.ElementTransformUtils.CopyElements(
                    source_doc,
                    List[DB.ElementId]([template_id]),
                    doc,
                    None,
                    options
                )

            else:
                forms.alert("Операция отменена пользователем.", title="Отмена")
                source_doc.Close(False)
                raise SystemExit()
        else:
            # Шаблон с таким именем не существует — просто копируем
            class CreateNewHandler(DB.IDuplicateTypeNamesHandler):
                def OnDuplicateTypeNamesFound(self, args):
                    return DB.DuplicateTypeAction.UseDestinationTypes  # если сработает, иначе UseDestinationTypes

            options = DB.CopyPasteOptions()
            options.SetDuplicateTypeNamesHandler(CreateNewHandler())

            DB.ElementTransformUtils.CopyElements(
                source_doc,
                List[DB.ElementId]([template_id]),
                doc,
                None,
                options
            
            )
    tr.Commit()        


# Сохраняем имена скопированных шаблонов, которые являются проверочными
copied_template_names = [t.Name for t in selected_templates if "роверка" in t.Name.lower()]

source_doc.Close(False)

# Получаем шаблоны вида из текущего документа (после копирования)
current_templates = {
    v.Name: v for v in DB.FilteredElementCollector(doc)
    .OfClass(DB.View)
    .WhereElementIsNotElementType()
    .ToElements()
    if v.IsTemplate
}



processed_3d_views = []  # Список созданных/обновлённых видов

if not operation_cancelled:
    with DB.Transaction(doc, "PS Создание проверочных 3D видов") as tr:
        tr.Start()
        
        for template_name in copied_template_names:
            # Найти шаблон вида в активном документе
            matching_template = next(
                (v for v in DB.FilteredElementCollector(doc)
                .OfClass(DB.View)
                .WhereElementIsNotElementType()
                if v.IsTemplate and v.Name == template_name),
                None
            )
            
            if not matching_template:
                continue  # шаблон не найден

            # Проверить, есть ли 3D вид с таким именем
            existing_3d_view = next(
                (v for v in DB.FilteredElementCollector(doc)
                .OfClass(DB.View3D)
                .WhereElementIsNotElementType()
                if not v.IsTemplate and v.Name == template_name),
                None
            )

            if existing_3d_view:
                # Применяем шаблон (если типы совпадают)
                if existing_3d_view.ViewType == matching_template.ViewType:
                    existing_3d_view.ViewTemplateId = matching_template.Id
                    
                    if existing_3d_view.GetTypeId() != created_type_id:
                        existing_3d_view.ChangeTypeId(created_type_id)
                    
                    processed_3d_views.append(existing_3d_view)
                else:
                    logger.warn("Тип шаблона '{}' не совместим с видом '{}'. Пропуск.".format(
                        template_name, existing_3d_view.Name))
            else:
                # Создаём новый 3D вид и применяем шаблон
                new_3d_view = DB.View3D.CreateIsometric(doc, created_type_id)
                new_3d_view.Name = template_name

                if new_3d_view.ViewType == matching_template.ViewType:
                    new_3d_view.ViewTemplateId = matching_template.Id
                    processed_3d_views.append(new_3d_view)
                else:
                    logger.warn("Тип шаблона '{}' не совместим с новым 3D видом '{}'. Пропуск.".format(
                        template_name, new_3d_view.Name))
        tr.Commit()            

# После транзакции — спрашиваем, открывать ли виды
if processed_3d_views:
    result = MessageBox.Show(
        "Созданы / обновлены проверочные 3D виды?\nОткрыть их?",
        "Открытие проверочных видов",
        MessageBoxButtons.YesNo,
        MessageBoxIcon.Question
    )

    if result == DialogResult.Yes:
        
        for view in processed_3d_views:
            uidoc.ActiveView = view

# Вне зависимости от processed_3d_views:
if not processed_3d_views and not operation_cancelled:
    forms.alert("Копирование завершено.", title="Готово")

if operation_cancelled:
    forms.alert("Операция была прервана пользователем.", title="Прерывание")