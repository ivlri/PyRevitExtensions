# -*- coding: utf-8 -*-
from pyrevit import forms
import os.path as op
import clr
import sys
import traceback
clr.AddReference('System')
clr.AddReference('System.Windows.Forms')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from System.Collections.ObjectModel import ObservableCollection
from System.ComponentModel import INotifyPropertyChanged
from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import forms, revit, HOST_APP
from operator import attrgetter


class WorksetItem:
    def __init__(self, name, workset_id, is_selected=False):
        self.Name = name
        self.WorksetId = workset_id
        self.IsSelected = is_selected


class WorksetVisibilityHandler(IExternalEventHandler):
    def __init__(self, panel, mode):
        self.panel = panel
        self.mode = mode
        
    def Execute(self, app):
        self.panel._set_wsvisible(mode = self.mode)

    def GetName(self):
        return "Workset Visibility Handler"


class WorksetsDockablePanel(forms.WPFPanel):
    panel_title = "Управление рабочими наборами"
    panel_id = "6b701dc2-47fb-4463-aae3-edcb7f8bef56"
    panel_source = op.join(op.dirname(__file__), "WorksetsDockablePanel.xaml")
    panel_doc = None

    def __init__(self):
        super(WorksetsDockablePanel, self).__init__()
        # Создание отдельных обработчиков на каждую кнопку. Иначе никак 
        self.hide_handler = WorksetVisibilityHandler(self, 'hide')
        self.show_handler = WorksetVisibilityHandler(self, 'show')
        self.hide_event = ExternalEvent.Create(self.hide_handler)
        self.show_event = ExternalEvent.Create(self.show_handler)

    def select_hide_click(self, sender, args):
        self.hide_event.Raise()

    def select_show_click(self, sender, args):
        self.show_event.Raise()

    def select_clear_click(self, sender, args):
        self._clear_selection()

    def update_panel(self, sender, args):
        doc = HOST_APP.doc
        self._setup_panel(doc)

    def _clear_selection(self):
        try:
            current_items = list(self.WorksetsListBox.ItemsSource)
            
            for item in current_items:
                item.IsSelected = False
            
            self.WorksetsListBox.ItemsSource = None
            self.WorksetsListBox.ItemsSource = current_items
        except Exception as ex:
            print(traceback.format_exc())

    def _setup_panel(self, doc):
        if doc != self.panel_doc and doc.IsWorkshared:
            try:
                all_worksets = ObservableCollection[object]()
                self.panel_doc = doc
                user_workset = FilteredWorksetCollector(self.panel_doc).\
                    OfKind(WorksetKind.UserWorkset)
                
                for workset in sorted(list(user_workset), key=attrgetter('Name')):
                    workset_item = WorksetItem(
                        name=workset.Name,
                        workset_id=workset.Id
                    )
                    all_worksets.Add(workset_item)

                self.WorksetsListBox.ItemsSource = all_worksets
            except Exception as ex:
                print(ex.message)
    
    def _get_selected(self):
        selected_items = [item for item in self.WorksetsListBox.ItemsSource 
                          if item.IsSelected]
        if not selected_items:
            forms.alert("Нет выбранных рабочих наборов!")
            return
        return selected_items
    
    def _set_wsvisible(self, mode='show'):
        try:
            active_view = self.panel_doc.ActiveView

            if mode == 'show':
                visible_mode = WorksetVisibility.Visible
                transaction_type = "PS_Показ наборов на виде"
            else:
                visible_mode = WorksetVisibility.Hidden
                transaction_type = "PS_Скрытие наборов на виде"

            with Transaction(self.panel_doc ,transaction_type) as t:
                t.Start()
                for item in self._get_selected():
                    #item.Name, item.WorksetId
                    active_view.SetWorksetVisibility(item.WorksetId, visible_mode)
                t.Commit()

        except Exception as ex:
            print(traceback.format_exc())

