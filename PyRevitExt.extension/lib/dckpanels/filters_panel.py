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
        self.panel._add_filters()

    def GetName(self):
        return "Add Filters Handler"

class AskQuestion(IExternalEventHandler):
    """
    Обработчик для всплывающего окна с вопросом 
    """

    def __init__(self, panel):
        self.panel = panel
        self.out = None
        
    def Execute(self, app):
        try:
            self.out = self.panel._is_template_using()
        except:
            print(traceback.format_exc())

    def GetName(self):
        return "Add Filters Handler"
    
    def _out(self):
        return self.out
    
# class FilterEnabledHandler(IExternalEventHandler):
#     """
#     Обработчик изменения состояния включения фильтра.
#     """

#     def __init__(self, panel):
#         self.panel = panel
#         self.filter_item = None
#         self.mode = None
        
#     def Execute(self, app):
#         if self.filter_item:
#             self.panel._set_filter_enable(self.filter_item, self.mode)

#     def GetName(self):
#         return "Filter Enabled Handler"


# class FilterVisibilityHandler(IExternalEventHandler):
#     """
#     Обработчик изменения видимости фильтра.
#     """

#     def __init__(self, panel):
#         self.panel = panel
#         self.filter_item = None
#         self.mode = None
        
#     def Execute(self, app):
#         if self.filter_item:
#             self.panel._set_filter_visibility(self.filter_item, self.mode)

#     def GetName(self):
#         return "Filter Visibility Handler"


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
        self.active_view = None
        self.temp_doc_mode = None
        self.temp_rvt_mode = None
        
        # Все действия что должны вызываться из основного потока 
        # self.enabled_handler = FilterEnabledHandler(self)
        # self.visibility_handler = FilterVisibilityHandler(self)

        self.view_settings_handler = FilterViewSettings(self)
        self.add_filters_handler = AddFiltersHandler(self)
        self.refresh_handler = RefreshPanelHandler(self)
        self.delete_handler = DeleteFilterHandler(self)
        self.question_handler = AskQuestion(self)

        # self.enabled_event = ExternalEvent.Create(self.enabled_handler)
        # self.visibility_event = ExternalEvent.Create(self.visibility_handler)

        self.view_settings_event = ExternalEvent.Create(self.view_settings_handler)
        self.add_filters_event = ExternalEvent.Create(self.add_filters_handler)
        self.refresh_event = ExternalEvent.Create(self.refresh_handler)
        self.delete_event = ExternalEvent.Create(self.delete_handler)
        self.question_event = ExternalEvent.Create(self.question_handler)

        # Для хранения текущего состояния
        self.current_filter_item = None
        self.current_mode = None

    # =================== UI-методы ===================

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
            if doc != self.doc:
                self.temp_doc_mode = None
                self.doc = doc

            view = self.doc.ActiveView
            temp_id = view.ViewTemplateId
            if (isinstance(temp_id, ElementId) 
                or (self.temp_rvt_mode or self.temp_doc_mode) 
                and not view.IsTemporaryViewPropertiesModeEnabled):
                self.active_view = doc.GetElement(temp_id)
            else:
                self.active_view = view
        except:
            print(traceback.format_exc())

        # print(self.doc.ActiveView.Name)
        self._setup_panel()

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
            with Transaction(self.doc, "Panel_Удалить фильтр из вида") as t:
                t.Start()
                self.active_view.RemoveFilter(filter_item.FilterElement.Id)
                t.Commit()
            
            self._setup_panel()
            
        except Exception as ex:
            print(traceback.format_exc())

    def _is_template_using(self):
        try:

            if self.temp_rvt_mode or self.temp_doc_mode:
                return None
            
            if self.active_view.IsTemporaryViewPropertiesModeEnabled:
                return None
            
            if not isinstance(self.active_view.ViewTemplateId, ElementId):
                return None

            commands = [
                CommandLink('Включить свойства временного вида', return_value="temporary_view"),
                CommandLink('Начать изменять шиблон, но только один раз', return_value="temp_one"),
                CommandLink('Начать изменять шаблон в пределах одного файла', return_value="temp_doc"),
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

            if choice == "temporary_view":
                with Transaction(self.doc, 'Panel_Временный вид') as t:
                    t.Start()
                    self.active_view.EnableTemporaryViewPropertiesMode(self.active_view.Id)
                    t.Commit()

                return True

            elif choice == "temp_one":
                return True

            elif choice == "temp_doc":
                self.temp_doc_mode = True

            elif choice == "temp_rvt":
                self.temp_rvt_mode = True

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
            self.question_event.self.Raise()
            check = self.question_handler._out()
            if self.temp_rvt_mode or self.temp_doc_mode or check:
                self.current_filter_item = sender.DataContext
                self.current_mode = mode
                
                # if handler_type == 'enable':
                #     self.enabled_handler.filter_item = self.current_filter_item
                #     self.enabled_handler.mode = mode
                #     self.enabled_event.Raise()
                # elif handler_type == 'visibility':
                #     self.visibility_handler.filter_item = self.current_filter_item
                #     self.visibility_handler.mode = mode
                #     self.visibility_event.Raise()

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
            all_filters = FilteredElementCollector(self.doc).OfClass(FilterElement).ToElements()

            filters_by_category = defaultdict(list)

            for f in all_filters:
                wrapper = FilterWrapper(f)

                cat_ids = f.GetCategories()  # List(ElementId)
                cat_name = self._get_filter_category(cat_ids, self.doc)
                filters_by_category[cat_name].append(wrapper)


            selected_filters = forms.SelectFromList.show(
                filters_by_category,
                title='Выбор фильтров для загрузки',
                multiselect=True,
                group_selector_title='Категории фильтр:',
                button_name='Подтвердить выбор!',
                sort_groups = 'sorted'
            )

            if selected_filters:
                with Transaction(self.doc, "Panel_Добавить фильтры") as t:
                    t.Start()
                    for selected_filter in selected_filters:
                        self.active_view.AddFilter(selected_filter.id)
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
            if t == "visibility":
                with Transaction(self.doc, "Panel_Настройка видимости фильтра") as t:
                    t.Start()
                    self.active_view.SetFilterVisibility(filter_item.FilterElement.Id, 
                                                        mode)
                    t.Commit()

            if t == "enable":
                with Transaction(self.doc, "Panel_Настройка активации фильтра") as t:
                    t.Start()
                    self.active_view.SetIsFilterEnabled(filter_item.FilterElement.Id, 
                                                        mode)
                    t.Commit()  
        except Exception as ex:
            print(traceback.format_exc())

    # def _set_filter_visibility(self,filter_item, mode):
    #     """
    #     Изменяет видимость фильтра на активном виде.

    #     Параметры
    #     ---------
    #     filter_item : FilterItem
    #         Элемент фильтра.
    #     mode : bool
    #         True - видимый, False - скрыт.

    #     Описание
    #     --------
    #     Выполняется транзакция Revit для применения видимости.
    #     """

    #     try:
    #         with Transaction(self.doc, "Настройка видимости фильтра") as t:
    #             t.Start()
    #             self.active_view.SetFilterVisibility(filter_item.FilterElement.Id, 
    #                                                 mode)
    #             t.Commit()
            
    #     except Exception as ex:
    #         print(traceback.format_exc())

    # def _set_filter_enable(self,filter_item, mode):
    #     """
    #     Включает или отключает фильтр на виде.

    #     Параметры
    #     ---------
    #     filter_item : FilterItem
    #         Элемент фильтра.
    #     mode : bool
    #         True - включен, False - выключен.

    #     Описание
    #     --------
    #     Выполняется транзакция Revit для изменения состояния фильтра.
    #     """

    #     try:
    #         with Transaction(self.doc, "Настройка активации фильтра") as t:
    #             t.Start()
    #             self.active_view.SetIsFilterEnabled(filter_item.FilterElement.Id, 
    #                                                 mode)
    #             t.Commit()
            
            
    #     except Exception as ex:
    #         print(traceback.format_exc())
    # def _is_template_using(self):

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
            view_filters = self.active_view.GetFilters()

            if view_filters:
                filters_tree = ObservableCollection[object]()
                # filters_tree.Add(FilterCategoryItem("Несколько категорий"))
                
                
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
                            view=self.active_view
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
                
        except InvalidOperationException:
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