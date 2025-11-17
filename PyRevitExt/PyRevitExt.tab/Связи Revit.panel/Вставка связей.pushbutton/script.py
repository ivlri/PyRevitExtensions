# -*- coding: utf-8 -*-
__title__   = "Cвязи: Загрузить"
__doc__ = "Описание: Функция быстрой погрузки связанных файлов в проект"
#==================================================
#IMPORTS
#==================================================

import os
import clr
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.Exceptions import InvalidOperationException
import sys
import re
#Forms 
import wpf
clr.AddReference("System")
from System.Windows import Window
from System.Windows.Controls import ComboBoxItem
from collections import OrderedDict
from pyrevit import coreutils
from pyrevit import versionmgr
from pyrevit.framework import ObservableCollection
from pyrevit.forms import TemplateListItem
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button,CheckBox, CommandLink, TaskDialog)
from collections import defaultdict, OrderedDict
from System.Collections.Generic import List
clr.AddReference('System.IO')
from pyrevit import forms
import math
# Добавляем логирование использования инструмента
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log() 

from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()


doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

PASS_FOLD = ["DIZ", "DWG", "Резерв", "Архив", "Analytic", "Координация и посадка",
             "backup", "Revit_temp", "99_"]

PROJECT_FOLDERS = {
    "АР": r"\03.AR",
    "КР": r"\04.KR",
    "ОВ": r"\05.MEP\05.4_HVAC",
    "ВК": r"\05.MEP\05.2+3_WSS",
    "ЭЛ": r"\05.MEP\05.1+5_ESS",
    "BS": r"\99.BIM",
    "TGL": r"|98.CRD\01_Tangl\Копии секций"
}

#=== Исправления потери контекста после открытия окна
import pyrevit
from pyrevit import DB, UI
from pyrevit import revit, forms, script
import wpf
from pyrevit import revit, forms, script
from System import EventHandler
from Autodesk.Revit.DB.Events import FailuresProcessingEventArgs

original_uiapp_property = pyrevit._HostApplication.uiapp
ui_app = UIApplication(__revit__.Application)  
@property
def custom_uiapp(self):
    """Return UIApplication provided to the running command."""
    return ui_app

pyrevit._HostApplication.uiapp = custom_uiapp

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
#==================================================
#FUNCTIONS
#==================================================
def is_cancel(doc, linkinst):
    """
    Проверка на отмену:
        Если нажать на отмену при вставку по координатам то ревит рандомно установить связь и даси имя площадки "не общедоступное"
    """
    if '<Не общедоступное>' in linkinst.Name:
        doc.Delete(linkinst.Id)
        return True
    else:
        linkinst.Pinned = True
        return False

def find_rvt_files(directory):
    files_found = []
    if not os.path.isdir(directory):
        return files_found

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not any(excl in d for excl in PASS_FOLD)]
        for f in files:
            if f.lower().endswith('.rvt'):
                files_found.append(os.path.join(root, f))
    return files_found


def build_base_folder(doc):
    """
    Получение базового расположения моделей
    """
    centralPath = doc.GetWorksharingCentralModelPath()
    file_path = ModelPathUtils.ConvertModelPathToUserVisiblePath(centralPath)
    if not file_path:
        forms.alert("Файл не сохранен на диске!!")
        sys.exit()
    if r"\\fs\bim\Projects" not in file_path:
        forms.alert(r"Загрузка возможна только внутри директории \\fs\bim\Projects")
        sys.exit()
    return "\\\\" + "\\".join(file_path.split("\\")[2:8])


def _create_revit_link(doc, fpath, wsnames="", mode='По координатам', copy_mode=False):
    """
    Создать RevitLinkType и вставить экземпляр(ы)
    """
    global not_load
    try:
        mpu = ModelPathUtils.ConvertUserVisiblePathToModelPath(fpath)
    except Exception as e:
        forms.alert("Неверный путь: {}\n{}".format(fpath, e))

    #--- Подготовка опций с конфигурацией рабочих наборов
    if wsnames:
        try:
            worksets = WorksharingUtils.GetUserWorksetInfo(mpu)
            ows = []
            wanted = [w.strip() for w in wsnames.split(',') if w.strip()]
            for ws in worksets:
                if not any(w in ws.Name for w in wanted):
                    ows.append(ws.Id)
            ws_ids = List[WorksetId](ows)
            wc = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
            wc.Open(ws_ids)
            link_options = RevitLinkOptions(True, wc)
        except:
            link_options = RevitLinkOptions("")
    else:
        link_options = RevitLinkOptions("")

    #--- Создание типа связи
    try:
        loadedLnkType = RevitLinkType.Create(doc, mpu, link_options)
    except Exception as e:
        raise
        # forms.alert("Не удалось создать тип связи для {}\n{}".format(fpath, e))

    #--- Загрузка экземпляра
    try:
        if mode == 'По координатам':
            pattern = r'([СCS]\d{2}.*)'
            names = []
            lnkInstance = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Shared)
            link_name = lnkInstance.Name
            cancel = is_cancel(doc,lnkInstance)

            if cancel:
                doc.Delete(loadedLnkType.ElementId)

            if 'побочная' in link_name.lower():
                # forms.alert("Была выбрана побочная площадка, имя не будет назначено!")
                pass
            else:
                try:
                    pos_name = link_name.split('позиция ')[-1]
                    sp_name = re.search(pattern, pos_name).group()[1:]
                    lnkInstance.LookupParameter("Имя").Set("Секция С" + sp_name)
                except:
                    pass

            if copy_mode and not cancel:
                names.append(lnkInstance.Name.split('позиция ')[-1])
                ln_doc = lnkInstance.GetLinkDocument()

                for pos in ln_doc.ProjectLocations:
                    pos_name = pos.Name
                    if "оформление" not in pos_name.lower() and pos_name not in names:
                        second = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Shared)
                        n = is_cancel(doc,second)
                        if not n:
                            names.append(second.Name.split('позиция ')[-1])
                        try:
                            second_linkinst_name = second.Name.split('позиция ')[-1]
                            sp_name = re.search(pattern, second_linkinst_name).group()[1:]
                            second.LookupParameter("Имя").Set("Секция С" +  sp_name)
                            second.Pinned = True
                        except:
                            doc.Delete(second.Id)

        else:
            #--- По базовой точке
            lnkInstance = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Origin)
            lnkInstance.MoveBasePointToHostBasePoint(False)

        return lnkInstance
    
    except InvalidOperationException:
        #--- Ошибка системы координат 

        # forms.alert("Ошибка: файл {} и проект в разных системах координат. Связь не вставлена.".format(link_name))
        not_load.append(loadedLnkType.GetModelName().ToString().split(r'\\')[-1])
        doc.Delete(loadedLnkType.ElementId)
    
    except Exception as e:
        forms.alert("Ошибка при вставке связи: {}\n{}".format(fpath, e))
        return False

# ==================================================
# UI: простой WPF-формат (оставляем как у тебя)
# ==================================================
import wpf
clr.AddReference("System")
from System.Windows import Window

class SimpleForm(Window):
    def __init__(self):
        path_xaml_file = os.path.join(os.path.dirname(__file__), 'FormUI.xaml')
        wpf.LoadComponent(self, path_xaml_file)
        self.ShowDialog()

    @property
    def ar_checked(self):
        return bool(self.UI_checkbox_1.IsChecked)

    @property
    def kr_checked(self):
        return bool(self.UI_checkbox_2.IsChecked)

    @property
    def ov_checked(self):
        return bool(self.UI_checkbox_3.IsChecked)

    @property
    def vk_checked(self):
        return bool(self.UI_checkbox_4.IsChecked)

    @property
    def ess_checked(self):
        return bool(self.UI_checkbox_5.IsChecked)

    @property
    def bs_checked(self):
        return bool(self.UI_checkbox_6.IsChecked)

    @property
    def use_all_sites(self):
        return bool(self.mode.IsChecked)

    @property
    def selected_mode(self):
        if self.UI_combobox.SelectedItem:
            return self.UI_combobox.SelectedItem.Content
        return None

    @property
    def close_sets_text(self):
        return self.UI_textbox_1.Text or ""

    def UIe_button_run(self, sender, e):
        self.Close()


# ==================================================
# MAIN
# ==================================================
base_folder = build_base_folder(doc)
form = SimpleForm()

# собираем выбранные секции
selected_sections = {
    "АР": form.ar_checked,
    "КР": form.kr_checked,
    "ОВ": form.ov_checked,
    "ВК": form.vk_checked,
    "BS": form.bs_checked,
}

mode = form.selected_mode
use_all_sites = form.use_all_sites
close_sets = form.close_sets_text

if mode == "По базовой точке" and use_all_sites:
    forms.alert('Использовать все площадки при вставке по базовой точке невозможно!!')
    sys.exit()

#---список папок для проверки
folders_to_check = {}
for key, enabled in selected_sections.items():
    if enabled and key in PROJECT_FOLDERS:
        folders_to_check[key] = os.path.join(base_folder, PROJECT_FOLDERS[key].lstrip('\\'))

#---если проект находится в Tangl
if "Tangl" in ModelPathUtils.ConvertModelPathToUserVisiblePath(doc.GetWorksharingCentralModelPath()):
    folders_to_check["TGL"] = os.path.join(base_folder, PROJECT_FOLDERS["TGL"].lstrip('\\'))

#---собираем все .rvt
all_found = []
for k, folder in folders_to_check.items():
    all_found.extend(find_rvt_files(folder))

dict_with_patches = {}
pattern_dict = OrderedDict()
existing_link_names = set()

doc_links = FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements()
existing_link_names.update([i.LookupParameter("Имя типа").AsString() for i in doc_links if i.LookupParameter("Имя типа")])
existing_link_names.add(doc.Title)

for key in sorted(folders_to_check.keys()):
    files = []
    folder_path = folders_to_check[key]
    for full in all_found:
        if full.startswith(folder_path):
            name = os.path.basename(full)
            if name not in existing_link_names:
                files.append(name)
                dict_with_patches[name] = full
    pattern_dict[key] = sorted(files, key=str.lower)

select_files = forms.SelectFromList.show(
    pattern_dict,
    title='Выбор файлов для загрузки',
    group_selector_title='Выберите файлы:',
    multiselect=True,
    button_name='Подтвердить выбор!',
    sort_groups='unsorted'
)

if not select_files:
    forms.alert("Файлы для загрузки не выбраны.")
    sys.exit()

files_to_load = [dict_with_patches[fname] for fname in select_files if fname in dict_with_patches]

doc_workset_table = doc.GetWorksetTable()
start_workset = doc_workset_table.GetActiveWorksetId()

fe_doc_workset = list(FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset))

workset_name_to_id = {ws.Name: ws.Id for ws in fe_doc_workset}

workset_search = {
    "AR": "AR",
    "AR_Rooms": "AR_Rooms",
    "SC_F": "SC_F",
    "SC_N": "SC_N",
    "SC_V": "SC_V",
    "SC_PP": "SC_V",
    "SC_FN": "SC_FN",
    "SC_NV": "SC_NV",
    "BS": "BS",
    "HVAC": "HVAC",
    "WSS": "WSS",
    "ESS": "ESS",
    "SC": "94_Связь_SC",
}

workset_dict = {}
missing_worksets = []
for short, pattern in workset_search.items():
    found = None
    for name, wid in workset_name_to_id.items():
        if pattern in name:
            found = wid
            break
    if found:
        workset_dict[short] = found
    else:
        missing_worksets.append(pattern)

instances = []
not_load = []
with forms.ProgressBar(title='Загрузка связей ({value} из {max_value})', cancellable=True) as pb:
    total = len(files_to_load)
    idx = 0
    t = Transaction(doc, 'Py_Добавление связей')


    t.Start()
    for fullpath in files_to_load:
        if pb.cancelled:
            break
        idx += 1
        pb.update_progress(idx, total)

        fname = os.path.basename(fullpath)
        parts = fname.split('_')
        chosen_ws_id = start_workset
        try:
            cat = parts[2] if len(parts) > 2 else None
            if cat and cat in workset_dict:
                chosen_ws_id = workset_dict[cat]
            elif cat and cat in workset_search:
                chosen_ws_id = workset_dict.get(cat, start_workset)
        except:
            chosen_ws_id = start_workset

        WorksetTable.SetActiveWorksetId(doc_workset_table, chosen_ws_id)

        link_inst = _create_revit_link(
            doc=doc,
            fpath=fullpath,
            wsnames="" if (os.path.basename(fullpath).startswith("BS") or "BS" in fname) else close_sets,
            mode=mode,
            copy_mode=use_all_sites,
        )

        WorksetTable.SetActiveWorksetId(doc_workset_table, start_workset)
    t.Commit()


    pyrevit._HostApplication.uiapp = original_uiapp_property
    if not_load:
        print("Количество не загруженных/частично загруженных связей:{}\n".format(len(not_load)))
        for i in not_load:
            print(i)

# forms.alert("Загружено связей: {}".format(len(instances)))


# # -*- coding: utf-8 -*-
# __title__   = "Cвязи: Загрузить"
# __doc__ = """Описание: Функция быстрой погрузки связанных файлов в проект"""

# #==================================================
# #IMPORTS
# #==================================================
# import os
# import clr
# from Autodesk.Revit.DB import *
# from Autodesk.Revit.UI import *
# from Autodesk.Revit.Exceptions import InvalidOperationException
# import sys
# import re
# #Forms 
# import wpf
# clr.AddReference("System")
# from System.Windows import Window
# from System.Windows.Controls import ComboBoxItem

# from pyrevit import coreutils
# from pyrevit import versionmgr
# from pyrevit.framework import ObservableCollection
# from pyrevit.forms import TemplateListItem
# from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
#                           Separator, Button,CheckBox, CommandLink, TaskDialog)
# from collections import defaultdict, OrderedDict
# from System.Collections.Generic import List
# clr.AddReference('System.IO')
# from pyrevit import forms
# import math
# import re
# # Добавляем логирование использования инструмента
# import os
# from functions._logger import ToolLogger
# ToolLogger(script_path=__file__).log() 

# doc   = __revit__.ActiveUIDocument.Document
# uidoc = __revit__.ActiveUIDocument
# app   = __revit__.Application
# uiapp   = __revit__
# act_view = doc.ActiveView

# PASS_FOLD = ["DIZ", "DWG", "Резерв", "Архив", "Analytic","Координация и посадка","backup","Revit_temp","99_"]

# #==============================================================
# #Customization SelectFromList to return all values in a groups
# #==============================================================

# def _prepare_context(self):
#         if isinstance(self._context, dict) and self._context.keys():
#             self._update_ctx_groups(self._context.keys())
#             new_ctx = {}
#             for ctx_grp, ctx_items in self._context.items():
#                 new_ctx[ctx_grp] = self._prepare_context_items(ctx_items)
#             self._context = new_ctx
#         else:
#             self._context = self._prepare_context_items(self._context)

# forms.SelectFromList._prepare_context = _prepare_context

# def _list_options(self, option_filter=None):
#     if option_filter:
#         self.checkall_b.Content = 'Выбрать все'
#         self.uncheckall_b.Content = 'Отменить все'
#         self.toggleall_b.Content = 'Обратить все'
#         # Get all items from all groups if context is a dict
#         if isinstance(self._context, dict):
#             self.all_items = [item for group in self._context.values() for item in group]
#         else:
#             self.all_items = self._context
#         # get a match score for every item and sort high to low
#         fuzzy_matches = sorted(
#             [(x,
#                 coreutils.fuzzy_search_ratio(
#                     target_string=x.name,
#                     sfilter=option_filter,
#                     regex=self.use_regex))
#                 for x in self.all_items],
#             key=lambda x: x[1],
#             reverse=True
#             )
#         # filter out any match with score less than 80
#         self.list_lb.ItemsSource = \
#             ObservableCollection[TemplateListItem](
#                 [x[0] for x in fuzzy_matches if x[1] >= 80]
#                 )
#     else:
#         self.checkall_b.Content = 'Выбрать все'
#         self.uncheckall_b.Content = 'Отменить все'
#         self.toggleall_b.Content = 'Обратить все'
#         self.list_lb.ItemsSource = \
#             ObservableCollection[TemplateListItem](self._get_active_ctx())

# forms.SelectFromList._list_options = _list_options

# def _get_options(self):
#     if self.multiselect:
#         if self.return_all:
#             return [x for x in self._get_active_ctx()]
#         else:
#             selected_items = []
#             if isinstance(self._context, dict):
#                 for group_items in self._context.values():
#                     selected_items.extend(
#                         item for item in group_items
#                         if item.state or item in self.list_lb.SelectedItems
#                     )
#             else:
#                 selected_items.extend(
#                     item for item in self._context
#                     if item.state or item in self.list_lb.SelectedItems
#                 )
#             return self._unwrap_options(selected_items)
#     else:
#         return self._unwrap_options([self.list_lb.SelectedItem])[0]

# forms.SelectFromList._get_options = _get_options

# #==================================================
# #FUNCTIONS
# #==================================================


# def find_rvt_files(directory):
#     rvt_files = []
#     for root, dirs, files in os.walk(directory):
#         path_parts = root.split(os.sep)

#         if any(any(excluded_folder in part for part in path_parts) for excluded_folder in PASS_FOLD):
#             continue
        
#         for file in files:
#             if file.lower().endswith('.rvt'):
#                 rvt_files.append(os.path.join(root, file))
#     return rvt_files


# def _linkmodel(fpath, doc, wsnames="", mode='По координатам', copy_mode=False):
#     """Create the Revit Link Type"""
#     mpu = ModelPathUtils.ConvertUserVisiblePathToModelPath(fpath)
#     # pattern = r'_([CS]\d{2})(?=_|$)'
#     pattern = r'([СCS]\d{2}.*)'
#     if wsnames:
#         #--- Workset configurations
#         try:
#             worksets = WorksharingUtils.GetUserWorksetInfo(mpu)
#             ows = []
#             for ws in worksets:
#                 link_name = ws.Name
#                 wsid = ws.Id
#                 closed = []	
#                 for wsn in wsnames.split(','):
#                     if wsn in link_name:
#                         closed.append(wsid)
#                 if wsid not in closed :
#                     ows.append(wsid)
		
#             ws_ids = List[WorksetId](ows)			
#             wc = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
#             link_options = RevitLinkOptions(True, wc)
#             wc2 = link_options.GetWorksetConfiguration()
#             wc2.Open(ws_ids)
#             link_options = RevitLinkOptions(True, wc2)
            
#         except :
#             link_options = RevitLinkOptions("")
#     else:
#         link_options = RevitLinkOptions("")

#     #--- Create RevitLinkType
#     loadedLnkType = RevitLinkType.Create(doc, mpu, link_options)

#     if mode == 'По координатам':
#         try:
#             lnkInstance = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Shared)
#             link_name = lnkInstance.Name

#             if 'побочная' in link_name.lower():
#                 # forms.alert("Была выбрана побочная площадка, имя не будет назначено!")
#                 pass
#             else:
#                 try:
#                     pos_name = link_name.split('позиция ')[-1]
#                     sp_name = re.search(pattern, link_name).group()[1:]
#                     lnkInstance.LookupParameter("Имя").Set("Секция С" + sp_name)
#                 except:
#                     pass

#             lnkInstance.Pinned = True
#         except InvalidOperationException:
#             forms.alert("Файл {} и связь {} находятся в разной системе координат!".format(doc.Title, doc.GetElement(loadedLnkType.ElementId).LookupParameter("Имя типа").AsString()), 
#                         sub_msg='Связь будет удалена!',
#                         title='Ошибка!')
#             doc.Delete(loadedLnkType.ElementId)
#             sys.exit()

#         if copy_mode:
#             ln_doc = lnkInstance.GetLinkDocument()
#             for pos in ln_doc.ProjectLocations:
#                 pos_name = pos.Name
#                 if pos_name not in link_name and "побочная" not in pos_name.lower():
#                     second_linkinst = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Shared)
#                     # print(second_linkinst)
#                     try:
#                         second_linkinst_name = second_linkinst.Name.split('позиция ')[-1]
#                         sp_name = re.search(pattern, second_linkinst_name).group()[1:]
#                         second_linkinst.LookupParameter("Имя").Set("Секция С" +  sp_name)
#                         second_linkinst.Pinned = True
#                     except:
#                         doc.Delete(second_linkinst.Id)
#     else:
#         lnkInstance = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Origin)
#         lnkInstance.MoveBasePointToHostBasePoint(False)
#         # link_base_point = BasePoint.GetProjectBasePoint(lnkInstance.GetLinkDocument())

#         # new_base = rotate_by_matrix(link_base_point.Position)
#         # ElementTransformUtils.MoveElement(doc, lnkInstance.Id, new_base)
#     return lnkInstance


# def rotate_by_matrix(xyz):
#     x = xyz.X
#     y = xyz.Y
#     z = xyz.Z

#     x1 = x*(-1) + 0*y
#     y1 = 0*x + (-1)*y

#     return XYZ(x1,y1,z)


# #==================================================
# #MAIN
# #==================================================
# class SimpleForm(Window):
#     def __init__(self):
#         path_xaml_file = os.path.join(os.path.dirname(__file__), 'FormUI.xaml')
#         wpf.LoadComponent(self, path_xaml_file)

#         self.ShowDialog()


#     @property
#     def ar_checked(self):
#         return self.UI_checkbox_1.IsChecked

#     @property
#     def kr_checked(self):
#         return self.UI_checkbox_2.IsChecked

#     @property
#     def ov_checked(self):
#         return self.UI_checkbox_3.IsChecked

#     @property
#     def vk_checked(self):
#         return self.UI_checkbox_4.IsChecked
    
#     @property
#     def ess_checked(self):
#         return self.UI_checkbox_5.IsChecked

#     @property
#     def bs_checked(self):
#         return self.UI_checkbox_6.IsChecked

#     @property
#     def use_all_sites(self):
#         return self.mode.IsChecked

#     @property
#     def selected_mode(self):
#         if self.UI_combobox.SelectedItem:
#             return self.UI_combobox.SelectedItem.Content
#         return None

#     @property
#     def close_sets_text(self):
#         return self.UI_textbox_1.Text

#     #==================================================
#     def UIe_button_run(self, sender, e):
#         """Обработчик нажатия кнопки 'Подтвердить!'"""
#         self.Close()

        
# #=== Set a patch (if the file is not in the Projects folder - will be alert)
# centralPath = doc.GetWorksharingCentralModelPath()
# file_patch = ModelPathUtils.ConvertModelPathToUserVisiblePath(centralPath)

# if not file_patch:
#     forms.alert("Файл не сохранен на диске!!")
#     sys.exit()
# if r"\\fs\bim\Projects" not in file_patch:
#     forms.alert(r"Загрузка возможна только внутри директории \\fs\bim\Projects")
#     sys.exit()

# folder = "\\\\" + "\\".join(file_patch.split("\\")[2:8])

# form = SimpleForm()

# # Значения после закрытия формы
# PROJECT_FOLDERS = {
#     "АР": r"\03.AR",
#     "КР": r"\04.KR",
#     "ОВ": r"\05.MEP\05.4_HVAC",
#     "ВК": r"\05.MEP\05.2+3_WSS",
#     "ЭЛ": r"\05.MEP\05.1+5_ESS",
#     "BS": r"\99.BIM",
#     "TGL":r"|98.CRD\01_Tangl\Копии секций"
# }

# selected_sections = {
#     "АР": form.ar_checked,
#     "КР": form.kr_checked,
#     "ОВ": form.ov_checked,
#     "ВК": form.vk_checked,
#     "BS": form.bs_checked,
# }

# mode = form.selected_mode
# use_all_sites = form.use_all_sites
# close_sets = form.close_sets_text

# if mode == "По базовой точке" and  use_all_sites:
#     forms.alert('Использовать все площадки при вставке по базовой точке невозможно!!')
#     sys.exit()

# # with forms.ProgressBar(indeterminate=True, cancellable=True) as pb:
# #     pb._title = 'Подготовка'
# folders_to_check = {}
# for key, value in selected_sections.items():
#     if value:
#         folders_to_check[key] = folder + PROJECT_FOLDERS[key]

# if "Tangl" in file_patch:
#     folders_to_check["TGL"] = folder + r"\98.CRD\01_Tangl\Копии секций"

# #=== Finding all the rtv files in folders
# dict_to_view = folders_to_check.copy()
# dict_with_patches = {}

# doc_links = FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements()
# links_to_pass = [i.LookupParameter("Имя типа").AsString() for i in doc_links]
# links_to_pass.append(doc.Title)

# for key, value in folders_to_check.items():
#     patches = find_rvt_files(value)
#     dict_to_view[key] = [pt.split("\\")[-1] for pt in patches if pt.split("\\")[-1] not in links_to_pass]
#     for pt in patches:
#         name = pt.split("\\")[-1]
#         if name not in links_to_pass:
#             dict_with_patches[name] = pt

# pattern_dict = OrderedDict((key, dict_to_view[key]) for key in sorted(dict_to_view.keys()))
# select_files = forms.SelectFromList.show(pattern_dict,
#             title='Выбор файлов для загрузки',
#             group_selector_title='Выберите файлы:',
#             multiselect=True,
#             button_name='Подтвердить выбор!'
#             # sort_groups='sorted' 
#         )

# if select_files:
#     files_to_load = [dict_with_patches[i] for i in select_files]

#     #=== Get WorksetTable and current workset
#     wstable = doc.GetWorksetTable()
#     activewsid = wstable.GetActiveWorksetId()

#     links = []
#     workset = {
#             "AR":"AR",
#             "AR_Rooms":"AR_Rooms",
#             "SC_F":"SC_F",
#             "SC_N":"SC_N",
#             "SC_V":"SC_V",
#             "SC_PP":"SC_V",
#             "SC_FN":"SC_FN",
#             "SC_NV":"SC_NV",
#             "BS":"BS",
#             "HVAC":"HVAC",
#             "WSS":"WSS",
#             "ESS":"ESS",
#             "SC":"94_Связь_SC",
#         }

#     doc_workset_table = doc.GetWorksetTable()
#     start_workset = doc_workset_table.GetActiveWorksetId()

#     #--- Сопоставление workset
#     doc_workset = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
#     fe_doc_workset = []
#     for i in doc_workset:
#         if "Связь" in i.Name:
#             fe_doc_workset.append(i)

#     workset_name_to_id = {ws.Name: ws.Id for ws in fe_doc_workset}

#     workset_dict = {}
#     passed_workset = []
#     for key, search_name in workset.items():
#         found_workset = None
#         for ws in fe_doc_workset:
#             if search_name in ws.Name:
#                 found_workset = ws
#                 break 

#         if found_workset:
#             workset_dict[key] = found_workset.Id
#         else:
#             passed_workset.append(search_name)
#     # if passed_workset:
#     #     forms.alert("Не найден рабочий набор, содержащий: \n{}".format('\n'.join(passed_workset)))

#     with forms.ProgressBar(title='Загрузка связей ({value} из {max_value})') as pb:
#         max_value = len(select_files)
#         count = 1
#         with Transaction(doc, 'Py_Добавление связей') as t:
#             t.Start()
#             for file in select_files:
#                 check = file.split("_")
#                 cat = check[2]

#                 if cat in passed_workset:
#                     file_workset = start_workset
#                 elif cat == "SC" or cat == "AR":
#                     try:
#                         file_workset = workset_dict['_'.join(check[2:4])]
#                     except:
#                         # file_workset = workset_dict[cat]
#                         file_workset = start_workset
#                 else:
#                     file_workset = workset_dict[cat]        

#                 WorksetTable.SetActiveWorksetId(doc_workset_table, file_workset)

#                 a = _linkmodel(dict_with_patches[file], 
#                                 doc, 
#                                 wsnames="" if cat == "BS" else close_sets, 
#                                 mode=mode, 
#                                 copy_mode=use_all_sites)
                
#                 links.append(a)
#                 count += 1
#                 pb.update_progress(count ,max_value)

#             WorksetTable.SetActiveWorksetId(doc_workset_table, start_workset)
#             t.Commit()
