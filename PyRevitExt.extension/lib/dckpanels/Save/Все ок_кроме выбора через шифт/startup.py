# -*- coding: utf-8 -*-
import clr
import sys
import os
import getpass
clr.AddReference('AdWindows')
import Autodesk.Windows as aw
from pyrevit import script

missed_users = ['gavrilovskaya', 'neustroeva']
def move_button_to_modify(sender, args):
    try:
        ribbon = aw.ComponentManager.Ribbon
        pyrevit_tab = next((t for t in ribbon.Tabs if t.Title == "PS_ALL"), None)

        # Пока не загрузится PyRevit будет пропускать выполнение
        if not pyrevit_tab:
            return  
        
        source_button = next(
            (item for panel in pyrevit_tab.Panels 
            for item in panel.Source.Items 
            if item.Text == "Обновлятор"),
            None
        )
        
        if not source_button:
            print("Кнопка 'PS_ALL/Обновлятор' не найдена!")
            __revit__.Idling -= move_button_to_modify 
            return
    
        modify_tab = next((t for t in ribbon.Tabs if t.Title == "Изменить" and t.IsVisible), None)
        existing_panels = any(p.Source.Title in ["Семейства", "Оформление"] for p in modify_tab.Panels)

        if modify_tab and not existing_panels:
            # Кнопка загрузки семейств
            new_button = aw.RibbonPanel()
            modify_tab.Panels.Add(new_button)
            new_button.Source = aw.RibbonPanelSource()
            new_button.Source.Title = "Семейства"
            cloned_button = source_button.Clone()
            new_button.Source.Items.Add(cloned_button)

            # отвязаться от события
            __revit__.Idling -= move_button_to_modify
        else:
            __revit__.Idling -= move_button_to_modify
            pass
        
    except Exception as ex:
        logger.error("Ошибка клонирования кнопки: {}".format(ex))
        __revit__.Idling -= move_button_to_modify

if getpass.getuser() not in missed_users:
    __revit__.Idling += move_button_to_modify


from dckpanels.workset_panel import WorksetsDockablePanel
from pyrevit import forms
from pyrevit import HOST_APP, framework
from pyrevit import revit, DB, UI



# if not forms.is_registered_dockable_panel(WorksetsDockablePanel):
# try:
panel = forms.register_dockable_panel(WorksetsDockablePanel, default_visible=True)
HOST_APP.uiapp.ViewActivated += \
    framework.EventHandler[UI.Events.ViewActivatedEventArgs](panel.update_panel)
# except Exception as ex:
#     print(ex.message)
