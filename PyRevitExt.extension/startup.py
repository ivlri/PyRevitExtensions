# -*- coding: utf-8 -*-
import clr
import sys
import os
import getpass
clr.AddReference('AdWindows')
import Autodesk.Windows as aw
from pyrevit import script

#==================================================
#Register button Family_Updater at "change" Revit panel
#==================================================
missed_users = ['gavrilovskaya', 'neustroeva']

def bdt_family_upload(sender, args):
    try:
        ribbon = aw.ComponentManager.Ribbon
        pyrevit_tab = next((t for t in ribbon.Tabs if t.Title == "PyRevitExt"), None)

        # Пока не загрузится PyRevit будет пропускать выполнение
        if not pyrevit_tab:
            return  
        
        source_button = next(
            (item for panel in pyrevit_tab.Panels 
            for item in panel.Source.Items 
            if item.Text == "Обновлятор"),
            None
        )
    
        modify_tab = next((t for t in ribbon.Tabs if t.Title == "Изменить" and t.IsVisible), None)
        existing_panels = any(p.Source.Title in ["Семейства", "Оформление"] for p in modify_tab.Panels)

        if modify_tab:
            # Кнопка загрузки семейств
            new_button = aw.RibbonPanel()
            modify_tab.Panels.Add(new_button)
            new_button.Source = aw.RibbonPanelSource()
            new_button.Source.Title = "Семейства"
            cloned_button = source_button.Clone()
            new_button.Source.Items.Add(cloned_button)

            # отвязаться от события
            __revit__.Idling -= bdt_family_upload
        else:
            __revit__.Idling -= bdt_family_upload
            pass
        
    except Exception as ex:
        __revit__.Idling -= bdt_family_upload

def decoration_panel(sender, args):
    try:
        ribbon = aw.ComponentManager.Ribbon
        pyrevit_tab = next((t for t in ribbon.Tabs if t.Title == "PyRevitExt"), None)

        # Пока не загрузится PyRevit будет пропускать выполнение
        if not pyrevit_tab:
            return  
        
        # Ищем панель "Оформление" в PyRevit
        source_panel = next(
            (panel for panel in pyrevit_tab.Panels 
             if panel.Source.Title == "Оформление"),
            None
        )
        
        modify_tab = next((t for t in ribbon.Tabs if t.Title == "Изменить" and t.IsVisible), None)

        if modify_tab and source_panel:
            # Проверяем, существует ли уже панель "Оформление"
            existing_panel = next((p for p in modify_tab.Panels if p.Source.Title == "Оформление"), None)
            
            if not existing_panel:
                # Создаем новую панель для оформления
                new_panel = aw.RibbonPanel()
                modify_tab.Panels.Add(new_panel)
                new_panel.Source = aw.RibbonPanelSource()
                new_panel.Source.Title = "Оформление"
                
                # Клонируем все элементы из исходной панели
                for item in source_panel.Source.Items:
                    cloned_item = item.Clone()
                    new_panel.Source.Items.Add(cloned_item)

            # отвязаться от события
            __revit__.Idling -= decoration_panel
        
    except Exception as ex:
        __revit__.Idling -= decoration_panel

if getpass.getuser() not in missed_users:
    __revit__.Idling += bdt_family_upload
    __revit__.Idling += decoration_panel


from dckpanels.workset_panel import WorksetsDockablePanel
from dckpanels.filters_panel import FiltersDockablePanel
from pyrevit import forms
from pyrevit import HOST_APP, framework
from pyrevit import revit, DB, UI

#==================================================
#Register panels
#==================================================
if forms.is_registered_dockable_panel(WorksetsDockablePanel) and forms.is_registered_dockable_panel(FiltersDockablePanel):
    worksets_panel = forms.register_dockable_panel(WorksetsDockablePanel, default_visible=True)
    filters_panel = forms.register_dockable_panel(FiltersDockablePanel, default_visible=True)

    HOST_APP.uiapp.ViewActivated += \
        framework.EventHandler[UI.Events.ViewActivatedEventArgs](worksets_panel.update_worksets)
    HOST_APP.uiapp.ViewActivated += \
        framework.EventHandler[UI.Events.ViewActivatedEventArgs](filters_panel.update_filters)

#==================================================
#Update pyrevot.forms.SelectFromList if pyrevit vers < 4.13? 
#==================================================
from pyrevit import coreutils
from pyrevit.framework import ObservableCollection
from pyrevit.forms import TemplateListItem
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button,CheckBox, CommandLink, TaskDialog)

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
