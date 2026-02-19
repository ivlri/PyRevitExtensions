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


# Создаем простое правило на "Комментарии", чтобы фильтр создался
# provider = ParameterValueProvider(
#     ElementId(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
# )
# evaluator = FilterStringContains()
# rule = FilterStringRule(provider, evaluator, "tmp", False)
# elem_filter = ElementParameterFilter(rule)
# print(elem_filter)
filter_name = "Новый фильтр_{}".format(int(time.time() * 1000))

# Подготовка пустых категорий и правила-заглушки (требуется для Revit 2021+)
cats = List[ElementId]()
with Transaction(doc, "Panel_Создать фильтр") as t:
    t.Start()
    f = ParameterFilterElement.Create(doc, filter_name ,cats)
    f_id = f.Id
    t.Commit()

new_filter = doc.GetElement(f_id)
print(new_filter)
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