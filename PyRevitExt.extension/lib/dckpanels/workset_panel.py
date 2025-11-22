# -*- coding: utf-8 -*-
from pyrevit import forms
import os.path as op
import clr
import sys
import traceback
clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from System.Collections.ObjectModel import ObservableCollection
from System.ComponentModel import INotifyPropertyChanged
from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import forms, revit, HOST_APP
# from operator import attrgetter

from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs
from System import EventHandler

import clr
clr.AddReference("System")
from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs
from System import EventHandler


class WorksetItem(INotifyPropertyChanged):
    """
    Модель элемента рабочего набора для отображения в WPF.

    Атрибуты
    --------
    Name : str
        Имя рабочего набора.
    WorksetId : Autodesk.Revit.DB.WorksetId
        Идентификатор рабочего набора.
    IsSelected : bool
        Флаг состояния выбора пользователем (checkbox).
    
    Описание
    --------
    Класс реализует интерфейс INotifyPropertyChanged, что позволяет
    автоматически обновлять привязанные элементы UI при изменении
    состояния (например, галочки IsSelected).
    """

    def __init__(self, name, workset_id, is_selected=False):
        self._name = name
        self._workset_id = workset_id
        self._is_selected = is_selected

    # объявление события изменения UI wpf
    def add_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Combine(self._propertyChanged, handler)

    def remove_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Remove(self._propertyChanged, handler)

    _propertyChanged = None

    def _raise(self, prop):
        if self._propertyChanged:
            self._propertyChanged(self, PropertyChangedEventArgs(prop))
    @property
    def Name(self):
        return self._name

    @property
    def WorksetId(self):
        return self._workset_id

    @property
    def IsSelected(self):
        return self._is_selected

    @IsSelected.setter
    def IsSelected(self, value):
        if self._is_selected != value:
            self._is_selected = value
            self._raise("IsSelected")

class WorksetVisibilityHandler(IExternalEventHandler):
    """
    Обработчик внешнего события Revit для изменения видимости рабочих наборов.

    Параметры
    ---------
    panel : WorksetsDockablePanel
        Ссылка на панель, где происходит выбор наборов.
    mode : str
        Режим работы: "show" или "hide".

    Описание
    --------
    Revit не позволяет выполнять транзакции из UI-потока WPF.
    Поэтому любое действие, изменяющее документ, выполняется через
    ExternalEvent → IExternalEventHandler → Execute().
    """

    def __init__(self, panel, mode):
        self.panel = panel
        self.mode = mode
        
    def Execute(self, app):
        self.panel._set_wsvisible(mode = self.mode)

    def GetName(self):
        return "Workset Visibility Handler"


class WorksetsDockablePanel(forms.WPFPanel):
    """
    Панель управления рабочими наборами.

    Назначение
    ----------
    Панель позволяет пользователю:
    - просматривать список пользовательских рабочих наборов,
    - выбирать несколько элементов,
    - скрывать/показывать их на активном виде.

    Особенности реализации
    ----------------------
    - Обновление списка рабочих наборов выполняется при событии ViewActivated.
    - Чтобы избежать лишних обращений, обновление происходит только при смене документа.
    - Действия, требующие транзакций, вынесены в ExternalEvent(обязательно для транзакций).
    """

    panel_title = "Управление рабочими наборами"
    panel_id = "6b701dc2-47fb-4463-aae3-edcb7f8bef56"
    panel_source = op.join(op.dirname(__file__), "WorksetsDockablePanel.xaml")
    panel_doc = None

    def __init__(self):
        super(WorksetsDockablePanel, self).__init__()
        """
        Инициализация отдельных обработчиков на каждую кнопку
        """

        self.hide_handler = WorksetVisibilityHandler(self, "hide")
        self.show_handler = WorksetVisibilityHandler(self, "show")

        self.hide_event = ExternalEvent.Create(self.hide_handler)
        self.show_event = ExternalEvent.Create(self.show_handler)

    def select_hide_click(self, sender, args):
        """
        UI-обработчик кнопки "Скрыть выбранные".

        Параметры
        ---------
        sender :
        args : 
        Не используется напрямую. Нужны для реализации в WPF

        Описание
        --------
        Вызывает связанный ExternalEvent,
        который выполнит скрытие рабочих наборов в документе.
        """
        
        self.hide_event.Raise()

    def select_show_click(self, sender, args):
        """
        UI-обработчик кнопки "Показать выбранные".

        Описание
        --------
        Вызывает связанный ExternalEvent,
        который выполнит показ рабочих наборов в документе.
        """

        self.show_event.Raise()

    def select_clear_click(self, sender, args):
        """
        UI-обработчик кнопки "Показать выбранные".

        Описание
        --------
        Вызывает метод сброса флажков IsSelected
        """

        self._refresh_selection()

    def update_worksets(self, sender, args):
        """
        UI-обработчик обновления списка рабочих наборов.

        Описание
        --------
        Вызывает метод обновления выделенных элементов
        """

        doc = HOST_APP.doc
        self._setup_panel(doc)

    def CheckBox_Checked(self, sender, args):
        """
        UI-обработчик активации CheckBox

        Описание
        --------
        Повторно загружает список рабочих наборов при смене документа
        """
                
        self._update_selected_items(True, sender)

    def CheckBox_Unchecked(self, sender, args):
        self._update_selected_items(False, sender)

    def _update_selected_items(self, is_checked, source_checkbox):
        """
        Обновляет состояние IsSelected для всех выделенных элементов списка.

        Параметры
        ---------
        is_checked : bool
            Новое состояние checkbox (True/False).
        source_checkbox : object
            Контрольный элемент UI, вызвавший событие (не используется напрямую).

        Описание
        --------
        Revit WPF ListBox может иметь множественный выбор.
        Если пользователь поставил/снял галочку у одного элемента,
        а выделено несколько - обновляются все выделенные.
        """

        try:
            if self.WorksetsListBox.SelectedItems.Count > 1:
                for item in self.WorksetsListBox.SelectedItems:
                    item.IsSelected = is_checked
        except Exception as ex:
            print(traceback.format_exc())

    def _refresh_selection(self):
        """
        Сбрасывает все отмеченные флажки IsSelected.

        Используется при нажатии кнопки «Очистить».
        """

        try:
            current_items = list(self.WorksetsListBox.ItemsSource)
            
            for item in current_items:
                item.IsSelected = False
            
            self.WorksetsListBox.ItemsSource = None
            self.WorksetsListBox.ItemsSource = current_items
        except Exception as ex:
            print(traceback.format_exc())

    def _setup_panel(self, doc):
        """
        Загружает список пользовательских рабочих наборов текущего документа.

        Параметры
        ---------
        doc : Autodesk.Revit.DB.Document
            Текущий документ Revit.

        Особенности
        -----------
        - Обновление выполняется только при смене документа.
        - Собираются только рабочие наборы типа UserWorkset.
        """

        if doc != self.panel_doc and doc.IsWorkshared:
            try:
                all_worksets = ObservableCollection[object]()
                self.panel_doc = doc
                user_workset = FilteredWorksetCollector(self.panel_doc).\
                    OfKind(WorksetKind.UserWorkset)
                
                for workset in sorted(list(user_workset), key=lambda x: x.Name):
                    workset_item = WorksetItem(
                        name=workset.Name,
                        workset_id=workset.Id
                    )
                    all_worksets.Add(workset_item)

                self.WorksetsListBox.ItemsSource = all_worksets
            except Exception as ex:
                print(ex.message)
    
    def _get_selected(self):
        """
        Возвращает список выбранных рабочих наборов.

        Если ничего не выбрано - показывает предупреждение.

        Возвращает
        ----------
        list[WorksetItem] | None
        """

        selected_items = [item for item in self.WorksetsListBox.ItemsSource 
                          if item.IsSelected]
        if not selected_items:
            forms.alert("Нет выбранных рабочих наборов!")
            return
        return selected_items
    
    def _set_wsvisible(self, mode="show"):
        """
        Изменяет видимость выбранных рабочих наборов на активном виде.

        Параметры
        ---------
        mode : str
            "show" - сделать видимыми,
            "hide" - скрыть.

        Описание
        --------
        Для каждого выбранного WorksetItem вызывается
        ActiveView.SetWorksetVisibility() внутри транзакции.
        """

        try:
            active_view = self.panel_doc.ActiveView

            if mode == "show":
                visible_mode = WorksetVisibility.Visible
                transaction_type = "PS_Показ наборов на виде"
            else:
                visible_mode = WorksetVisibility.Hidden
                transaction_type = "PS_Скрытие наборов на виде"

            items = self._get_selected()
            with Transaction(self.panel_doc ,transaction_type) as t:
                t.Start()
                if items:
                    for item in items:
                        #item.Name, item.WorksetId
                        active_view.SetWorksetVisibility(item.WorksetId, visible_mode)
                t.Commit()

        except Exception as ex:
            print(traceback.format_exc())

