# -*- coding: utf-8 -*-
from dckpanels.workset_panel import WorksetsDockablePanel
from dckpanels.filters_panel import FiltersDockablePanel
from pyrevit import forms, revit
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from operator import attrgetter
import Autodesk.Windows as aw
from System.Collections.Generic import List
import random, string, time
# forms.register_dockable_panel(FiltersDockablePanel, default_visible=True)
# forms.open_dockable_panel(FiltersDockablePanel.panel_id)

# ribbon = aw.ComponentManager.Ribbon
#
doc = revit.doc


# import clr
# clr.AddReference('RevitAPI')
# from Autodesk.Revit.DB import UnitUtils, UnitTypeId
# doc = __revit__.ActiveUIDocument.Document
# print(UnitUtils.ConvertToInternalUnits(1200, UnitTypeId.))
# -*- coding: utf-8 -*-
"""
Отладка UnitTypeId для BuiltInParameter Revit
Работает с Revit 2022+
"""

from Autodesk.Revit.DB import BuiltInParameter, UnitUtils, UnitTypeId
from Autodesk.Revit.DB import Document, FilteredElementCollector

# --- Кэш для ускорения ---
_bip_cache = {}

# --- Основные функции ---
def get_bip_unit_type(doc, param_id):
    int_val = param_id.IntegerValue

    if int_val in _bip_cache:
        return _bip_cache[int_val]

    st_str, spec = _get_bip_storage_info(doc, param_id)
    print("DEBUG_get_bip_storage_info: bip {} | st_str {} | spec {}".format(param_id, st_str, spec))

    # fallback для специальных числовых параметров
    if spec is None and st_str == "number":
        if param_id == BuiltInParameter.CURVE_ELEM_LENGTH:
            spec = UnitTypeId.Meters
        elif param_id == BuiltInParameter.ROOM_AREA:
            spec = UnitTypeId.SquareMeters
        elif param_id == BuiltInParameter.ALL_MODEL_COST:
            spec = UnitTypeId.Currency

    _bip_cache[int_val] = spec
    return spec

def _get_bip_storage_info(doc, param_id):
    stmap = _get_storage_type_map()
    try:
        forge_id = ParameterUtils.GetParameterTypeId(param_id)
        st = doc.GetTypeOfStorage(forge_id)
        st_str = stmap.get(st, "string")
        spec = _get_spec_from_forge_id(forge_id, st_str)
        return (st_str, spec)
    except Exception:
        return ("string", None)

def _get_spec_from_forge_id(forge_id, storage_type):
    if storage_type != "number" or not forge_id:
        return None
    try:
        if UnitUtils.IsMeasurableSpec(forge_id):
            return forge_id
    except Exception:
        pass
    return None

def _get_storage_type_map():
    return {
        0: "none",
        1: "integer",
        2: "number",
        3: "string",
        4: "element_id"
    }

# --- Скрипт для теста ---
def test_bip_units(doc):
    test_params = [
        BuiltInParameter.CURVE_ELEM_LENGTH,
        BuiltInParameter.ROOM_AREA,
        BuiltInParameter.ALL_MODEL_COST,
    ]

    for bip in test_params:
        unit_type = get_bip_unit_type(doc, bip)
        print("BIP {} → UnitTypeId: {}".format(bip, unit_type))

# --- Запуск скрипта в Revit ---
if __name__ == "__main__":
    # doc — активный документ Revit, например через pyRevit:
    # from pyrevit import revit
    # doc = revit.doc

    # Для RevitPythonShell используем __revit__.ActiveUIDocument.Document
    try:
        doc = __revit__.ActiveUIDocument.Document
    except NameError:
        print("Документ Revit не найден. Используй pyRevit или RevitPythonShell.")
        doc = None

    if doc:
        test_bip_units(doc)
#-------------------------------------------------------------------------------------------
# from pyrevit import forms, revit
# from Autodesk.Revit.DB import *

#Крутой пример ООП что бы не напрягяться с выбором pyrevit
# class FilterWrapper:
#     def __init__(self, filter_element):
#         self.filter_element = filter_element
#         self.name = filter_element.Name
#         self.id = filter_element.Id
        
#     def __str__(self):
#         return self.name

# doc = revit.doc
# active_view = doc.ActiveView

# all_filters = FilteredElementCollector(doc).OfClass(FilterElement).ToElements()

# # Создаем список оберток
# filter_wrappers = [FilterWrapper(f) for f in sorted(all_filters, key=lambda x: x.Name)]

# selected_filters = forms.SelectFromList.show(
#     filter_wrappers,
#     title='Выбор фильтров для загрузки',
#     multiselect=True,
#     button_name='Подтвердить выбор!'
# )

# with Transaction(doc, "Добавить фильтры") as t:
#     t.Start()
#     for selected_filter in selected_filters:
#         active_view.AddFilter(selected_filter.id)
#     t.Commit()