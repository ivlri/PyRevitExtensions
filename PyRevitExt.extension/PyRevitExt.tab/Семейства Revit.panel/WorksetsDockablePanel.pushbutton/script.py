# -*- coding: utf-8 -*-
from dckpanels.workset_panel import WorksetsDockablePanel
from dckpanels.filters_panel import FiltersDockablePanel
from pyrevit import forms
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from operator import attrgetter
import Autodesk.Windows as aw
# ws_panel_id = WorksetsDockablePanel.panel_id
# forms.open_dockable_panel(WorksetsDockablePanel.panel_id)
# forms.open_dockable_panel(FiltersDockablePanel.panel_id)
# forms.register_dockable_panel(FiltersDockablePanel, default_visible=True)

ribbon = aw.ComponentManager.Ribbon
pyrevit_tab = next((t for t in ribbon.Tabs if t.Title == "PyRevitExt"), None)
cc = 0
for panel in pyrevit_tab.Panels:
    print(panel.Source.Title)
    # for i in dir(panel):
    #     print(i)
    for item in panel.Source.Items:
        print("         {}".format(item))
        print("         └── {}".format(item.Text))

        if cc == 1:
            for i in dir(item):
                print(i)

            break
    if cc == 1:
        break
    cc += 1
# from pyrevit import revit
# uiapp = __revit__
# panels = uiapp.GetRibbonPanels("PyRevitExt")
# for p in panels:
#     print("PANEL: {}".format(p.Name))
#     for item in p.GetItems():
#         print("   └── {}".format(item.ItemText))

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