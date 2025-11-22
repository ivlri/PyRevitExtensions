
# -*- coding: utf-8 -*-
__title__   = "Cвязи: Обновить из"
__doc__ = """Описание: Функция быстрой замены связанных файлов"""

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

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
uiapp   = __revit__
act_view = doc.ActiveView

PASS_FOLD = ["DIZ", "DWG", "Резерв", "Архив", "Analytic","Координация и посадка","backup","Revit_temp","99_"]

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

def find_rvt_files(directory):
    rvt_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not any(excl in d for excl in PASS_FOLD)]
        for f in files:
            if f.lower().endswith(".rvt"):
                rvt_files.append(os.path.join(root, f))
    return rvt_files


def get_base_project_folder(doc):
    central_path = doc.GetWorksharingCentralModelPath()
    file_path = ModelPathUtils.ConvertModelPathToUserVisiblePath(central_path)

    if not file_path or r"\\fs\bim\Projects" not in file_path:
        forms.alert("Файл должен быть сохранён в \\\\fs\\bim\\Projects")
        sys.exit()

    return "\\\\" + "\\".join(file_path.split("\\")[2:8])


def get_selected_links(doc):
    linktypes = FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements()
    names = {
        lt.LookupParameter("Имя типа").AsValueString().split(".rvt")[0]: lt
        for lt in linktypes
    }
    selected = forms.SelectFromList.show(
        list(names.keys()),
        title="Выбор связей для обновления",
        multiselect=True,
        button_name="Подтвердить выбор",
        sort_groups='sorted'
    )
    if not selected:
        sys.exit()
    return {n: names[n] for n in selected}


def match_files_to_links(folder, links):
    all_files = find_rvt_files(folder)
    all_names = {os.path.basename(f): f for f in all_files}

    grouped = {}
    link_map = {}
    path_map = {}

    for name, link in links.items():
        for key, sub in PROJECT_FOLDERS.items():
            if key in name:
                matching = sorted([f for f in all_names.keys() if key in f], key=str.lower)
                for fname in matching:
                    link_map[fname] = link
                    path_map[fname] = all_names[fname]

                grouped[name] = matching

    grouped = OrderedDict(sorted(grouped.items(), key=lambda x: x[0].lower()))

    return grouped, link_map, path_map

def reload_links(select_files, fnames_link, fnames_folder):
    total = len(select_files)
    with forms.ProgressBar(
        title="Замена связей ({value} из {max_value})",
        cancellable=True
    ) as pb:
        for i, fname in enumerate(select_files, start=1):
            if pb.cancelled:
                break
            pb.update_progress(i, total)

            try:
                new_path = fnames_folder[fname]
                link_type = fnames_link[fname]
                model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(new_path)

                ows = []
                mpu = ModelPathUtils.ConvertUserVisiblePathToModelPath(new_path)
                worksets = WorksharingUtils.GetUserWorksetInfo(model_path)

                for ws in worksets:
                    link_name = ws.Name
                    wsid = ws.Id
                    closed = []	
                    for wsn in "00_,01_,02_,03_,99_,Связь".split(','):
                        if wsn in link_name:
                            closed.append(wsid)
                    if wsid not in closed :
                        ows.append(wsid)

                ws_ids = List[WorksetId](ows)			
                if "BS" not in fname:
                    wc = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
                    wc.Open(ws_ids)
                else:
                    wc = WorksetConfiguration(WorksetConfigurationOption.OpenAllWorksets)

                link_type.LoadFrom(model_path, wc)

            except Exception as e:
                forms.alert(u"Ошибка при загрузке '{}':\n{}".format(fname, e))

# ==================================================
# SETTINGS
# ==================================================
PASS_FOLD = [
    "DIZ", "DWG", "Резерв", "Архив", "Analytic", "Координация и посадка",
    "backup", "Revit_temp", "99_"
]

PROJECT_FOLDERS = {
    "AR": r"\03.AR",
    "SC": r"\04.KR",
    "AS": r"\04.KR",
    "HVAC": r"\05.MEP\05.4_HVAC",
    "WSS": r"\05.MEP\05.2+3_WSS",
    "BS": r"\99.BIM"
}

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
# ==================================================
# MAIN
# ==================================================
base_folder = get_base_project_folder(doc)
links = get_selected_links(doc)

grouped_files, fnames_link, fnames_folder = match_files_to_links(base_folder, links)


selected_files = forms.SelectFromList.show(
    grouped_files,
    title="Выбор файлов для загрузки",
    group_selector_title="Сопоставьте файлы:",
    multiselect=True,
    button_name="Подтвердить выбор",
    sort_groups='sorted'
)

if selected_files:
    reload_links(selected_files, fnames_link, fnames_folder)

pyrevit._HostApplication.uiapp = original_uiapp_property
# # -*- coding: utf-8 -*-
# __title__   = "Cвязи: Обновить из"
# __doc__ = """Описание: Функция быстрой замены связанных файлов"""

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


# #==================================================
# #MAIN
# #==================================================
# centralPath = doc.GetWorksharingCentralModelPath()
# file_patch = ModelPathUtils.ConvertModelPathToUserVisiblePath(centralPath)

# if not file_patch:
#     forms.alert("Файл не сохранен на диске!!")
#     sys.exit()
# if r"\\fs\bim\Projects" not in file_patch:
#     forms.alert(r"Замена возможна только внутри директории \\fs\bim\Projects")
#     sys.exit()

# #=== Selecting a linktype for upload
# doc_linktypes = FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements()
# linktypes_names = {
#     lnt.LookupParameter('Имя типа').AsValueString().split('.rvt')[0]:lnt
#     for lnt in doc_linktypes
# }

# types_upload = forms.SelectFromList.show(list(linktypes_names.keys()),
#                     title='Выбор связей для обновления',
#                     group_selector_title='Выберите связь:',
#                     multiselect=True,
#                     button_name='Подтвердить выбор!'
#                 )

# select_links = [linktypes_names[name] for name in types_upload]
    
# #=== Set a patch (if the file is not in the Projects folder - will be alert)
# centralPath = doc.GetWorksharingCentralModelPath()
# file_patch = ModelPathUtils.ConvertModelPathToUserVisiblePath(centralPath)

# folder = "\\\\" + "\\".join(file_patch.split("\\")[2:8])

# # Значения после закрытия формы 1
# PROJECT_FOLDERS = {
#     "AR": r"\03.AR",
#     "SC": r"\04.KR",
#     "AS": r"\04.KR",
#     "HVAC": r"\05.MEP\05.4_HVAC",
#     "WSS": r"\05.MEP\05.2+3_WSS",
#     "BS": r"\99.BIM"
#     # "TGL":r"|98.CRD\01_Tangl\Копии секций"
# }

# lnname_foldersname = {}
# fnames_link = {}
# fnames_folder = {}
# for ln in select_links:
#     ln_name = ln.LookupParameter('Имя типа').AsValueString().split('.rvt')[0]
#     fnames = []
#     for key, fold in PROJECT_FOLDERS.items():
#         if key in ln_name:
#             patches = find_rvt_files(folder + PROJECT_FOLDERS[key])
#             for pt in patches:
#                 pt_name = pt.split("\\")[-1]
#                 fnames.append(pt.split("\\")[-1])
#                 fnames_link[pt_name] = ln
#                 fnames_folder[pt_name] = pt

#     lnname_foldersname[ln_name] = fnames


# select_files = forms.SelectFromList.show(lnname_foldersname,
#             title='Выбор файлов для загрузки',
#             group_selector_title='Сопоставьте файлы:',
#             multiselect=True,
#             button_name='Подтвердить выбор!'
#             # sort_groups='sorted' 
#         ) # вернет только список выбраных элементов потм надо вернуть исходную связь

# with forms.ProgressBar(indeterminate=True, cancellable=True) as pb:
#     pb._title = 'Подготовка'
# # with forms.ProgressBar(title='Замена связей ({value} из {max_value})') as pb:
#     # max_value = len(select_files)
#     # count = 1
#     for new_file in select_files:
#         new_fpath = fnames_folder[new_file]
#         link_to_upload = fnames_link[new_file]

#         if "BS" not in new_file:
#             mpu = ModelPathUtils.ConvertUserVisiblePathToModelPath(new_fpath)
#             worksets = WorksharingUtils.GetUserWorksetInfo(mpu)
#             ows = []

#             for ws in worksets:
#                 link_name = ws.Name
#                 wsid = ws.Id
#                 closed = []	
#                 for wsn in "00_,01_,02_,03_,99_,Связь".split(','):
#                     if wsn in link_name:
#                         closed.append(wsid)
#                 if wsid not in closed :
#                     ows.append(wsid)

#             ws_ids = List[WorksetId](ows)			
#             wc = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
#             wc.Open(ws_ids)
            
#         link_to_upload.LoadFrom(mpu,wc)

#         # count += 1
#         # pb.update_progress(count ,max_value)

