# -*- coding: utf-8 -*-
__title__   = "Cвязи"
__doc__ = """Описание: Функция быстрой погрузки связанных файлов в проект"""

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

PROJECT_FOLDERS = {
    "AR": r"\03.AR",
    "KR": r"\04.KR",
    "MEP_HVAC": r"\05.MEP\05.4_HVAC",
    "MEP_WSS": r"\05.MEP\05.2+3_WSS",
    "BIM": r"\99.BIM"
}
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
        path_parts = root.split(os.sep)

        if any(any(excluded_folder in part for part in path_parts) for excluded_folder in PASS_FOLD):
            continue
        
        for file in files:
            if file.lower().endswith('.rvt'):
                rvt_files.append(os.path.join(root, file))
    return rvt_files


def _linkmodel(fpath, doc, wsnames="", mode='По координатам', copy_mode=False):
    """Create the Revit Link Type"""
    mpu = ModelPathUtils.ConvertUserVisiblePathToModelPath(fpath)
    
    if wsnames:
        #--- Workset configurations
        try:
            worksets = WorksharingUtils.GetUserWorksetInfo(mpu)
            ows = []
            for ws in worksets:
                link_name = ws.Name
                wsid = ws.Id
                closed = []	
                for wsn in wsnames.split(','):
                    if wsn in link_name:
                        closed.append(wsid)
                if wsid not in closed :
                    ows.append(wsid)
		
            ws_ids = List[WorksetId](ows)			
            wc = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
            link_options = RevitLinkOptions(True, wc)
            wc2 = link_options.GetWorksetConfiguration()
            wc2.Open(ws_ids)
            link_options = RevitLinkOptions(True, wc2)
            
        except :
            link_options = RevitLinkOptions("")
    else:
        link_options = RevitLinkOptions("")

    #--- Create RevitLinkType
    loadedLnkType = RevitLinkType.Create(doc, mpu, link_options)

    if mode == 'По координатам':
        try:
            lnkInstance = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Shared)
            link_name = lnkInstance.Name

            if 'побочная' in link_name.lower():
                forms.alert("Была выбрана побочная площадка, имя не будет назначено!")
            else:
                sp_name = link_name.Split('_')[-1]
                lnkInstance.LookupParameter("Имя").Set("Секция " + str(int(sp_name[-2:])))

            lnkInstance.Pinned = True
        except InvalidOperationException:
            forms.alert("Файл {} и связь {} находятся в разной системе координат!".format(doc.Title, doc.GetElement(loadedLnkType.ElementId).LookupParameter("Имя типа").AsString()), 
                        sub_msg='Связь будет удалена!',
                        title='Ошибка!')
            doc.Delete(loadedLnkType.ElementId)
            sys.exit()

        if copy_mode:
            ln_doc = lnkInstance.GetLinkDocument()
            for pos in ln_doc.ProjectLocations:
                pos_name = pos.Name
                if pos_name not in link_name and "побочная" not in pos_name.lower():
                    second_linkinst = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Shared)
                    # print(second_linkinst)
                    try:
                        second_linkinst_name = second_linkinst.Name.Split('_')[-1]
                        second_linkinst.LookupParameter("Имя").Set("Секция " + str(int(second_linkinst_name[-2:])))
                        second_linkinst.Pinned = True
                    except:
                        doc.Delete(second_linkinst.Id)
    else:
        lnkInstance = RevitLinkInstance.Create(doc, loadedLnkType.ElementId, ImportPlacement.Origin)
        link_base_point = BasePoint.GetProjectBasePoint(lnkInstance.GetLinkDocument())

        new_base = rotate_by_matrix(link_base_point.Position)
        ElementTransformUtils.MoveElement(doc, lnkInstance.Id, new_base)
    return lnkInstance


def rotate_by_matrix(xyz):
    x = xyz.X
    y = xyz.Y
    z = xyz.Z

    x1 = x*(-1) + 0*y
    y1 = 0*x + (-1)*y

    return XYZ(x1,y1,z)


#==================================================
#MAIN
#==================================================

#=== Set a patch (if the file is not in the Projects folder - will be alert)
centralPath = doc.GetWorksharingCentralModelPath()
file_patch = ModelPathUtils.ConvertModelPathToUserVisiblePath(centralPath)

if not file_patch:
    forms.alert("Файл не сохранен на диске!!")
    sys.exit()
if r"\\fs\bim\Projects" not in file_patch:
    forms.alert(r"Вставка возможна только внутри директории \\fs\bim\Projects")
    sys.exit()

folder = "\\\\" + "\\".join(file_patch.split("\\")[2:8])

components = [
            Label('Выберете нужные разделы:',top_offset=-10),
            CheckBox('AR', 'АР', default=False),
            CheckBox('KR', 'КР', default=False),
            CheckBox('MEP_HVAC', 'ОВ', default=False),
            CheckBox('MEP_WSS', 'ВК', default=False),
            CheckBox('BIM', 'BIM', default=False),
            Separator(),
            Label('Выберите режим загрузки:',top_offset=-10),
            ComboBox('add_mode', ["По координатам","По базовой точке"], sort=False),
            CheckBox('copy_mode', 'Использовать все площадки?', default=False),
            Separator(),
            Label('Какие наборы закрыть(Не затрагивает BS):',top_offset=-10),
			TextBox('close_ws', Text="00_,01_,02_,03_,Связь"),
            Separator(),
            Button('Подтвердить выбор', on_click=False)
            ]

form = FlexForm('Выбор шаблона', components)
form.show()

try:
    if form.values['add_mode'] == "По базовой точке" and  form.values['copy_mode']:
        forms.alert('Использовать все площадки при вставке по базовой точке невозможно!!')
        sys.exit()
except:
    sys.exit()

with forms.ProgressBar(indeterminate=True, cancellable=True) as pb:
    pb._title = 'Подготовка'
    folders_to_check = {}
    for key, value in form.values.items():
        if value and key not in ['add_mode', 'close_ws', 'copy_mode']:
            folders_to_check[key] = folder + PROJECT_FOLDERS[key]

    #=== Finding all the rtv files in folders
    dict_to_view = folders_to_check.copy()
    dict_with_patches = {}

    doc_links = FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements()
    links_to_pass = [i.LookupParameter("Имя типа").AsString() for i in doc_links]
    links_to_pass.append(doc.Title)

    for key, value in folders_to_check.items():
        patches = find_rvt_files(value)
        dict_to_view[key] = [pt.split("\\")[-1] for pt in patches if pt.split("\\")[-1] not in links_to_pass]
        for pt in patches:
            name = pt.split("\\")[-1]
            if name not in links_to_pass:
                dict_with_patches[name] = pt

    pattern_dict = OrderedDict((key, dict_to_view[key]) for key in sorted(dict_to_view.keys()))
    select_files = forms.SelectFromList.show(pattern_dict,
                title='Выбор файлов для загрузки',
                group_selector_title='Выберите файлы:',
                multiselect=True,
                button_name='Подтвердить выбор!'
                # sort_groups='sorted' 
            )

    if select_files:
        files_to_load = [dict_with_patches[i] for i in select_files]

        #=== Get WorksetTable and current workset
        wstable = doc.GetWorksetTable()
        activewsid = wstable.GetActiveWorksetId()

        links = []
        workset = {
                "AR":"AR",
                "AR_Rooms":"AR_Rooms",
                "SC_F":"SC_F",
                "SC_N":"SC_N",
                "SC_V":"SC_V",
                "SC_PP":"SC_V",
                "SC_FN":"SC_FN",
                "SC_NV":"SC_NV",
                "BS":"BS",
                "HVAC":"HVAC",
                "WSS":"WSS",
                "ESS":"ESS",
                "SC":"94_Связь_SC",
            }

        doc_workset_table = doc.GetWorksetTable()
        start_workset = doc_workset_table.GetActiveWorksetId()

        #--- Сопоставление workset
        doc_workset = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
        fe_doc_workset = []
        for i in doc_workset:
            if "Связь" in i.Name:
                fe_doc_workset.append(i)

        workset_name_to_id = {ws.Name: ws.Id for ws in fe_doc_workset}

        workset_dict = {}
        passed_workset = []
        for key, search_name in workset.items():
            found_workset = None
            for ws in fe_doc_workset:
                if search_name in ws.Name:
                    found_workset = ws
                    break 

            if found_workset:
                workset_dict[key] = found_workset.Id
            else:
                passed_workset.append(search_name)
        # if passed_workset:
        #     forms.alert("Не найден рабочий набор, содержащий: \n{}".format('\n'.join(passed_workset)))

        with forms.ProgressBar(title='Вставка связей ({value} из {max_value})') as pb:
            max_value = len(select_files)
            count = 1
            with Transaction(doc, 'Py_Добавление связей') as t:
                t.Start()
                for file in select_files:
                    check = file.split("_")
                    cat = check[2]

                    if cat in passed_workset:
                        file_workset = start_workset
                    elif cat == "SC" or cat == "AR":
                        try:
                            file_workset = workset_dict['_'.join(check[2:4])]
                        except:
                            file_workset = workset_dict[cat]
                    else:
                        file_workset = workset_dict[cat]        

                    WorksetTable.SetActiveWorksetId(doc_workset_table, file_workset)

                    mode = form.values['add_mode']
                    a = _linkmodel(dict_with_patches[file], 
                                   doc, 
                                   wsnames="" if cat == "BS" else form.values['close_ws'], 
                                   mode=mode, 
                                   copy_mode=form.values['copy_mode'])
                    
                    links.append(a)
                    count += 1
                    pb.update_progress(count ,max_value)

                WorksetTable.SetActiveWorksetId(doc_workset_table, start_workset)
                t.Commit()