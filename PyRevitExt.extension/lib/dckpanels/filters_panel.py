# -*- coding: utf-8 -*-
from pyrevit import forms
import os.path as op
import clr
import sys
import traceback
from collections import defaultdict

clr.AddReference('System')
clr.AddReference('System.Windows.Forms')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from System.Collections.ObjectModel import ObservableCollection
from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs
from System import EventHandler

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.Exceptions import InvalidOperationException
from pyrevit import forms, revit, HOST_APP
from operator import attrgetter
from rpw.ui.forms import CommandLink, TaskDialog
<<<<<<< HEAD

# #==================================================
# #Update pyrevot.forms.SelectFromList if pyrevit vers < 4.13? 
# #==================================================
from pyrevit import coreutils, forms
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

=======
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da

class FilterCategoryItem(INotifyPropertyChanged):
    """
    Модель элемента категории для панели фильтров (уровень 1).

    Атрибуты
    --------
    Name : str
        Имя категории.
    Children : ObservableCollection[object]
        Список дочерних элементов фильтров.
    IsExpanded : bool
        Флаг развёрнутости в дереве UI.
    IsCategory : bool
        Флаг для XAML, указывающий что это категория.
    IsFilter : bool
        Флаг для XAML, всегда False для категории.

    Описание
    --------
    Реализует интерфейс INotifyPropertyChanged, что позволяет
    автоматически обновлять привязанные элементы UI при изменении состояния.
    """

    def __init__(self, name):
        self._name = name
        self._children = ObservableCollection[object]()
        self._is_expanded = True

        # XAML bindings
        self._is_category = True
        self._is_filter = False

        self._propertyChanged = None

    @property
    def Name(self):
        return self._name

    @property
    def Children(self):
        return self._children

    @property
    def IsExpanded(self):
        return self._is_expanded

    @IsExpanded.setter
    def IsExpanded(self, value):
        if self._is_expanded != value:
            self._is_expanded = value
            self._raise("IsExpanded")

    @property
    def IsCategory(self):
        return self._is_category

    @property
    def IsFilter(self):
        return self._is_filter

    # INotifyPropertyChanged
    def add_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Combine(self._propertyChanged, handler)

    def remove_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Remove(self._propertyChanged, handler)

    def _raise(self, prop):
        if self._propertyChanged:
            self._propertyChanged(self, PropertyChangedEventArgs(prop))


class FilterItem(INotifyPropertyChanged):
    """
    Модель элемента фильтра (уровень 2).

    Атрибуты
    --------
    Name : str
        Имя фильтра.
    FilterElement : Autodesk.Revit.DB.FilterElement
        Элемент фильтра Revit.
    IsFilterEnabled : bool
        Состояние включения фильтра на виде.
    FilterVisibility : bool
        Состояние видимости фильтра на виде.
    IsCategory : bool
        Флаг для XAML, всегда False для фильтра.
    IsFilter : bool
        Флаг для XAML, всегда True для фильтра.

    Описание
    --------
    Реализует INotifyPropertyChanged для привязки данных WPF.
    Обновляет состояние фильтра на виде через чекбоксы в панели.
    """
       
    def __init__(self, name, filter_element, view):
        self._name = name
        self._filter_element = filter_element
        self._view = view
        
        # Состояния фильтра на виде
        self._is_filter_enabled = view.GetIsFilterEnabled(filter_element.Id)
        self._filter_visibility = view.GetFilterVisibility(filter_element.Id)

        # XAML bindings
        self._is_category = False
        self._is_filter = True

        self._propertyChanged = None

    # ========== Базовые свойства ==========
    @property
    def Name(self):
        return self._name

    @property
    def FilterElement(self):
        return self._filter_element

    # --- Состояние включения фильтра ---
    @property
    def IsFilterEnabled(self):
        return self._is_filter_enabled

    @IsFilterEnabled.setter
    def IsFilterEnabled(self, value):
        if self._is_filter_enabled != value:
            self._is_filter_enabled = value
            self._raise("IsFilterEnabled")

    # --- Видимость фильтра ---
    @property
    def FilterVisibility(self):
        return self._filter_visibility

    @FilterVisibility.setter
    def FilterVisibility(self, value):
        if self._filter_visibility != value:
            self._filter_visibility = value
            self._raise("FilterVisibility")

    # ------- XAML type flags -------
    @property
    def IsCategory(self):
        return self._is_category

    @property
    def IsFilter(self):
        return self._is_filter

    # INotifyPropertyChanged
    def add_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Combine(self._propertyChanged, handler)

    def remove_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Remove(self._propertyChanged, handler)

    def _raise(self, prop):
        if self._propertyChanged:
            self._propertyChanged(self, PropertyChangedEventArgs(prop))


# ===================== Обработчики ExternalEvent =====================
class RefreshPanelHandler(IExternalEventHandler):
    """
    Обработчик для обновления панели фильтров.
    """
    
    def __init__(self, panel):
        self.panel = panel
        
    def Execute(self, app):
        try:
            self.panel.update_filters(None, None)
        except:
            print(traceback.format_exc())
        # self.panel._setup_panel()

    def GetName(self):
        return "Refresh Panel Handler"


class AddFiltersHandler(IExternalEventHandler):
    """
    Обработчик для добавления фильтров на вид.
    """

    def __init__(self, panel):
        self.panel = panel
        
    def Execute(self, app):
        check = self.panel._is_template_using()
        if check:
            self.panel._add_filters()

    def GetName(self):
        return "Add Filters Handler"


class FilterViewSettings(IExternalEventHandler):
    """
    Обработчик изменения видимости фильтра.
    """

    def __init__(self, panel):
        self.panel = panel
        self.filter_item = None
        self.setting_type = None
        self.mode = None
        
    def Execute(self, app):
        if self.filter_item:
            check = self.panel._is_template_using()
            if check:
                self.panel._set_filter_settings(self.filter_item, self.setting_type ,self.mode)

    def GetName(self):
        return "Filter View Settings Handler"


class DeleteFilterHandler(IExternalEventHandler):
    """
    Обработчик удаления фильтра с вида.
    """

    def __init__(self, panel):
        self.panel = panel
        self.filter_item = None
        
    def Execute(self, app):
        if self.filter_item:
            self.panel._delete_filter(self.filter_item)

    def GetName(self):
        return "Delete Filter Handler"
    

class FilterWrapper:
    """
    Обертка для элемента фильтра Revit.

    Атрибуты
    --------
    filter_element : FilterElement
        Элемент фильтра Revit.
    name : str
        Имя фильтра.
    id : ElementId
        Идентификатор фильтра.
    """

    def __init__(self, filter_element):
        self.filter_element = filter_element
        self.name = filter_element.Name
        self.id = filter_element.Id
        
    def __str__(self):
        return self.name


class FiltersDockablePanel(forms.WPFPanel):
    """
    Панель управления фильтрами Revit.

    Назначение
    ----------
    Позволяет пользователю:
    - включать/отключать фильтры,
    - изменять их видимость,
    - добавлять новые фильтры,
    - удалять фильтры с вида.

    Особенности реализации
    ----------------------
    - Для операций с документом используется ExternalEvent.
    - Поддерживается множественный выбор и обновление UI через INotifyPropertyChanged.
    - Фильтры группируются по категориям ElementFilter.
    """

    panel_title = "Управление фильтрами"
    panel_id = "7c801dc2-58fb-4463-bbe3-edcb7f8bef57"
    panel_source = op.join(op.dirname(__file__), "FiltersDockablePanel.xaml")

    def __init__(self):
        super(FiltersDockablePanel, self).__init__()
        self.doc = None
        self.doc_title = None
        self.active_view = None
        self.active_view_template = None
        self.is_temporary = None
        self.is_template = None

        self.temp_doc_mode = None
<<<<<<< HEAD
        self.temp_docs = {}
=======
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
        self.temp_doc_one = None
        self.temp_rvt_mode = None
        self.activate_temporary_view = None
        
        # Все действия что должны вызываться из основного потока 
        self.view_settings_handler = FilterViewSettings(self)
        self.add_filters_handler = AddFiltersHandler(self)
        self.refresh_handler = RefreshPanelHandler(self)
        self.delete_handler = DeleteFilterHandler(self)

        self.view_settings_event = ExternalEvent.Create(self.view_settings_handler)
        self.add_filters_event = ExternalEvent.Create(self.add_filters_handler)
        self.refresh_event = ExternalEvent.Create(self.refresh_handler)
        self.delete_event = ExternalEvent.Create(self.delete_handler)

        # Для хранения текущего состояния
        self.current_filter_item = None
        self.current_mode = None

    # =================== UI-методы ===================
    # ----- Обновления -----
    # !!! Все что заппускается из под WPF долджно иметь sender, args
    # И не стоит разделять UIRevit выполнение на несколько функций
    def update_filters(self, sender, args):
        """
        Обновляет панель фильтров через RevitEvent.

        Параметры
        ---------
        sender : object
            Элемент, вызвавший событие.
        args : object
            Аргументы события (не используются напрямую).

        Описание
        --------
        Получает текущий документ и активный вид Revit,
        после чего инициализирует панель фильтров через `_setup_panel()`.
        """
        try:
            doc = HOST_APP.doc
<<<<<<< HEAD
            doc_t = doc.Title

            if self.doc_title != doc_t :
                self.doc = doc
                self.doc_title = self.doc.Title

            # self._determine_target_view()
            # if doc_t not in self.temp_docs:
            #     self.temp_doc_mode = None
            # else:
            #     self.temp_doc_mode = True

            # view = self.doc.ActiveView
            # temp_id = view.ViewTemplateId

            # # Обновление части флагов действий
            # self.is_temporary = view.IsTemporaryViewPropertiesModeEnabled()
            # self.is_template = False if temp_id == ElementId.InvalidElementId else True

            # # получение вида
            # self.active_view = view # всегда получает активный
            # self.active_view_template = doc.GetElement(temp_id)
=======
            if doc != self.doc:
                self.temp_doc_mode = None
                self.doc = doc

            view = self.doc.ActiveView
            temp_id = view.ViewTemplateId

            # Обновление части флагов действий
            self.is_temporary = view.IsTemporaryViewPropertiesModeEnabled()
            self.temp_doc_one = None
            self.activate_temporary_view = None
            self.is_template = False if temp_id == ElementId.InvalidElementId else True

            # получение вида
            self.active_view = view # всегда получает активный
            self.active_view_template = doc.GetElement(temp_id)

            # Подписать активный вид
            v = self._determine_target_view()
            v_name = "[Вид]_" + v.Name
            if self.temp_rvt_mode:
                v_name = "[Шаблон|Весь сеанс]_" + v.Name
            if self.temp_doc_mode:
                v_name = "[Шаблон|Документ]_" + v.Name

            self.ViewNameTextBlock.Text = v_name
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da

            self._setup_panel()
        except:
            print(traceback.format_exc())

<<<<<<< HEAD
    def _determine_target_view(self, mode=None):

        view = self.doc.ActiveView
        temp_id = view.ViewTemplateId

        # Обновление части флагов действий
        self.is_temporary = view.IsTemporaryViewPropertiesModeEnabled()
        self.is_template = False if temp_id == ElementId.InvalidElementId else True

        if not self.is_template or self.is_temporary:
            return view
        else:
            return self.doc.GetElement(temp_id)

        # if not self.is_template or self.is_temporary:
        #     return self.active_view
        
        # return self.active_view_template
=======
    def _determine_target_view(self):
        # if self.is_temporary:
        #     return self.active_view

        if self.temp_doc_one or self.temp_doc_mode or self.temp_rvt_mode:
            return self.active_view_template
        
        return self.active_view
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da

    # ----- Обработчики чекбоксов -----

    def filter_enabled_checked(self, sender, args):
        """
        UI-обработчик включения фильтра.

        Описание
        --------
        Активирует фильтр на виде, используя ExternalEvent.
        """

        self._setup_handler(sender, 'enable', True)

    def filter_enabled_unchecked(self, sender, args):
        """
        UI-обработчик отключения фильтра.

        Описание
        --------
        Деактивирует фильтр на виде через ExternalEvent.
        """

        self._setup_handler(sender, 'enable', False)

    def filter_visibility_checked(self, sender, args):
        """
        UI-обработчик включения видимости фильтра.

        Описание
        --------
        Делает фильтр видимым на виде через ExternalEvent.
        """

        self._setup_handler(sender, 'visibility', True)

    def filter_visibility_unchecked(self, sender, args):
        """
        UI-обработчик отключения видимости фильтра.

        Описание
        --------
        Скрывает фильтр на виде через ExternalEvent.
        """

        self._setup_handler(sender, 'visibility', False)

    # ----- Обработчики кнопок -----

    def btn_add_filters(self, sender, args):
        """
        UI-обработчик кнопки "Добавить фильтры".

        Описание
        --------
        Запускает ExternalEvent для добавления выбранных фильтров на активный вид.
        """
        self.add_filters_event.Raise()

    def btn_refresh_panel(self, sender, args):
        """
        UI-обработчик кнопки "Обновить панель".

        Описание
        --------
        Принудительно обновляет панель фильтров через ExternalEvent.
        """
<<<<<<< HEAD
        # self.temp_rvt_mode = None
=======
        self.temp_rvt_mode = None
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
        self.refresh_event.Raise()
        
    def btn_expand_all_click(self, sender, args):
        """
        UI-обработчик кнопки "Развернуть все категории".

        Описание
        --------
        Разворачивает все категории фильтров на панели.
        """

        self._expand_all_categories(True)

    def btn_collapse_all_click(self, sender, args):
        """
        UI-обработчик кнопки "Свернуть все категории".

        Описание
        --------
        Сворачивает все категории фильтров на панели.
        """

        self._expand_all_categories(False)

    def btn_delete_filter_click(self, sender, args):
        """
        UI-обработчик кнопки удаления фильтра.

        Параметры
        ---------
        sender : object
            Кнопка, вызвавшая событие. Данные фильтра берутся из `sender.DataContext`.
        args : object
            Аргументы события (не используются напрямую).

        Описание
        --------
        Устанавливает текущий фильтр для удаления и вызывает ExternalEvent удаления.
        """

        try:
            filter_item = sender.DataContext
            self.delete_handler.filter_item = filter_item
            self.delete_event.Raise()
        except Exception as ex:
            print(traceback.format_exc())

    # =================== Внутренние методы ===================

    def _delete_filter(self, filter_item):
        """
        Удаляет фильтр с активного вида.

        Параметры
        ---------
        filter_item : FilterItem
            Элемент фильтра для удаления.

        Описание
        --------
        Выполняется транзакция Revit для удаления фильтра,
        после чего обновляется панель через `_setup_panel()`.
        """

        try:
            target_view = self._determine_target_view()
            with Transaction(self.doc, "Panel_Удалить фильтр из вида") as t:
                t.Start()
                target_view.RemoveFilter(filter_item.FilterElement.Id)
                t.Commit()
            
            self._setup_panel()
            
        except Exception as ex:
            print(traceback.format_exc())

    def _is_template_using(self):
        try:
            if (
            self.is_temporary 
            or self.temp_doc_mode 
            or self.temp_rvt_mode
            or self.activate_temporary_view
            or not self.is_template
            ):
                return True
            
            commands = [
                CommandLink('Включить свойства временного вида', return_value="temporary_view"),
<<<<<<< HEAD
                # CommandLink('Начать изменять шаблон, но только один раз', return_value="temp_one"),
                # CommandLink('Начать изменять шаблон в пределах одного файла', return_value="temp_doc"),
=======
                CommandLink('Начать изменять шаблон, но только один раз', return_value="temp_one"),
                CommandLink('Начать изменять шаблон в пределах одного файла', return_value="temp_doc"),
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
                CommandLink('Начать изменять шаблон в текущем сеансе Revit', return_value="temp_rvt")
            ]

            dialog = TaskDialog(
                "На текущем виде применён шаблон вида.",
                title_prefix=False,
                content="Выберите дальнейшее действие!",
                commands=commands,
                show_close=True
            )

            choice = dialog.show()

            if choice is None:
<<<<<<< HEAD
                self._setup_panel()
=======
                self.update_filters(None,None)
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
                return False  

            if choice == "temporary_view":
                with Transaction(self.doc, "PL_Временный вид") as t:
                    t.Start()
<<<<<<< HEAD
                    active_view = self.doc.ActiveView
                    active_view.EnableTemporaryViewPropertiesMode(active_view.Id)
                    t.Commit()

            # elif choice == "temp_one":
            #     self.temp_doc_one = True

            # elif choice == "temp_doc":
            #     self.temp_doc_mode = True
            #     self.temp_docs[self.doc_title] = self.doc
            #     # self.temp_docs.append(self.doc_title)

            elif choice == "temp_rvt":
                self.temp_rvt_mode = True
            
            self._setup_panel()
=======
                    self.active_view.EnableTemporaryViewPropertiesMode(self.active_view.Id)
                    t.Commit()


            elif choice == "temp_one":
                self.temp_doc_one = True

            elif choice == "temp_doc":
                self.temp_doc_mode = True

            elif choice == "temp_rvt":
                self.temp_rvt_mode = True
                
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
            return True
        except Exception as ex:
            print(traceback.format_exc())

    def _setup_handler(self, sender, handler_type, mode):
        """
        Настраивает обработчик ExternalEvent для фильтра.

        Параметры
        ---------
        sender : object
            Элемент UI, вызвавший событие.
        handler_type : str
            Тип обработки: 'enable' или 'visibility'.
        mode : bool
            Новое состояние фильтра.

        Описание
        --------
        Устанавливает текущий фильтр и режим для соответствующего обработчика
        и инициирует ExternalEvent.
        """
        
        try:
            self.current_filter_item = sender.DataContext
            self.current_mode = mode
    
            self.view_settings_handler.filter_item = self.current_filter_item
            self.view_settings_handler.mode = mode
            self.view_settings_handler.setting_type = handler_type
            self.view_settings_event.Raise()
                
        except Exception as ex:
            print(traceback.format_exc())

    def _add_filters(self):
        """
        Добавляет выбранные фильтры на активный вид.

        Описание
        --------
        Вызывает форму выбора фильтров, добавляет выбранные фильтры на вид
        через транзакцию Revit и обновляет панель.
        """
        try:
            target_view = self._determine_target_view()

            all_filters = FilteredElementCollector(self.doc).OfClass(FilterElement).ToElements()
            view_filters = target_view.GetFilters()
            filters_by_category = defaultdict(list)

            for f in all_filters:
                if f not in view_filters:
                    wrapper = FilterWrapper(f)

                    cat_ids = f.GetCategories()  # List(ElementId)
                    cat_name = self._get_filter_category(cat_ids, self.doc)
                    filters_by_category[cat_name].append(wrapper)


            selected_filters = forms.SelectFromList.show(
                filters_by_category,
                title='Выбор фильтров для загрузки',
                multiselect=True,
                group_selector_title='Категории фильтров:',
                button_name='Подтвердить выбор!',
                sort_groups = 'sorted'
            )

            if selected_filters:
                with Transaction(self.doc, "Panel_Добавить фильтры") as t:
                    t.Start()
                    for selected_filter in selected_filters:
                        target_view.AddFilter(selected_filter.id)
<<<<<<< HEAD
                        target_view.SetFilterVisibility(selected_filter.id, 
                                                        False)
=======
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
                    t.Commit()
                
                self._setup_panel()

        except Exception as ex:
            print(traceback.format_exc())

    def _set_filter_settings(self,filter_item,t, mode):
        """
        Обертка для изменения видимости фильтра на активном виде.

        Параметры
        ---------
        filter_item : FilterItem
            Элемент фильтра.
        t: string
            Тип обработки: 'enable' или 'visibility'.
        mode : bool
            True - видимый, False - скрыт.

        Описание
        --------
        Переводит на транзакции Revit для применения видимости.
        """
        try:
            target_view = self._determine_target_view()

            if t == "visibility":
                with Transaction(self.doc, "Panel_Настройка видимости фильтра") as t:
                    t.Start()
                    target_view.SetFilterVisibility(filter_item.FilterElement.Id, 
                                                        mode)
                    t.Commit()

            if t == "enable":
                with Transaction(self.doc, "Panel_Настройка активации фильтра") as t:
                    t.Start()
                    target_view.SetIsFilterEnabled(filter_item.FilterElement.Id, 
                                                        mode)
                    t.Commit()  

<<<<<<< HEAD
            self._setup_panel()
=======
            self.update_filters(None,None)
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
        except Exception as ex:
            print(traceback.format_exc())

    def _setup_panel(self):
        """
        Инициализация панели фильтров с группировкой по категориям.

        Описание
        --------
        - Загружает все фильтры активного вида.
        - Группирует их по категориям ElementFilter.
        - Создает дерево категорий и фильтров для отображения в WPF TreeView.
        """

        try:
<<<<<<< HEAD
            target_view = self._determine_target_view(mode='setup')

            # Подписать активный вид
            target_view_name = target_view.Name
            pref = "[Вид]_"

            if self.temp_rvt_mode and not self.is_temporary and self.is_template:
                pref = "[Шаблон|Весь сеанс]_"
            # if self.temp_doc_mode:
            #     v_name = "[Шаблон|Документ]_" + target_view_name
            if self.is_temporary:
                pref = "[Временный вид]_"

            v_name = pref + target_view_name
            self.ViewNameTextBlock.Text = v_name

=======
            target_view = self._determine_target_view()
>>>>>>> 97cbef8db0e1c9fcc8218beb214d62e795f425da
            view_filters = target_view.GetFilters()

            if view_filters:
                filters_tree = ObservableCollection[object]()
     
                # Группируем фильтры по их ElementFilter (категориям)
                categories_dict = {}
                
                for filter_id in view_filters:
                    filter_element = self.doc.GetElement(filter_id)
                    
                    if not filter_element or not isinstance(filter_element, ParameterFilterElement):
                        continue
                        
                    try:
                        element_cats = filter_element.GetCategories()
                        category_name = self._get_filter_category(element_cats, self.doc)
                        
                        # Создаем категорию если ее нет
                        if category_name not in categories_dict:
                            categories_dict[category_name] = FilterCategoryItem(category_name)
                        
                        # Создание элемента фильтра
                        filter_item = FilterItem(
                            name=filter_element.Name,
                            filter_element=filter_element,
                            view=target_view
                        )
                        
                        categories_dict[category_name].Children.Add(filter_item)
                        
                    except Exception as ex:
                        print(traceback.format_exc())
                        continue
                
                # Добавляем категории в дерево
                if categories_dict:
                    for category_item in sorted(categories_dict.values(), key=lambda x: x.Name):
                        filters_tree.Add(category_item)
                    
                    self.FiltersTreeView.ItemsSource = filters_tree
                else:
                    # Если словарь категорий пуст - очистка панели
                    self.FiltersTreeView.ItemsSource = ObservableCollection[object]()
            else:
                self.FiltersTreeView.ItemsSource = ObservableCollection[object]()
            
        except Exception:
            self.FiltersTreeView.ItemsSource = ObservableCollection[object]()
            # print(traceback.format_exc())

    def _get_filter_category(self, categories, doc):
        """
        Определяет имя категории фильтра.

        Параметры
        ---------
        categories : IList[Category]
            Список категорий фильтра.
        doc : Document
            Документ Revit для поиска имен категорий.

        Возвращает
        -------
        str
            Имя категории фильтра.
        """

        if not categories:
            return "Без категории"
        
        if len(categories) == 1:
            return Category.GetCategory(doc, categories[0]).Name
        
        return "Несколько категорий" 

    # Вспомогательные методы
    def _expand_all_categories(self, expand):
        """
        Разворачивает или сворачивает все категории на панели.

        Параметры
        ---------
        expand : bool
            True - развернуть, False - свернуть.
        """

        if self.FiltersTreeView.ItemsSource:
            for category in self.FiltersTreeView.ItemsSource:
                category.IsExpanded = expand
                

