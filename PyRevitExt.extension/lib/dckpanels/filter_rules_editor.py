# -*- coding: utf-8 -*-
"""Filter rules editor — modal WPF window for editing ParameterFilterElement rules."""

import traceback

import clr

clr.AddReference("System")
clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")
clr.AddReference("System.Xml")
clr.AddReference("RevitAPI")
import System.Windows as WinNS
import System.Windows.Controls as Controls
from Autodesk.Revit.DB import *
from pyrevit import forms
from pyrevit.forms import WPFWindow
from System import EventHandler
from System.Collections.Generic import List
from System.Collections.ObjectModel import ObservableCollection
from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs
from System.IO import StringReader
from System.Windows.Markup import XamlReader
from System.Xml import XmlReader

# =================== Operator definitions ===================

# Maps evaluator class -> (display_name, param_type)
STRING_OPERATORS = [
    ("равно", "str_equals"),
    ("не равно", "str_not_equals"),
    ("содержит", "str_contains"),
    ("не содержит", "str_not_contains"),
    ("начинается с", "str_begins"),
    ("заканчивается на", "str_ends"),
]

NUMERIC_OPERATORS = [
    ("равно", "num_equals"),
    ("не равно", "num_not_equals"),
    ("больше", "num_greater"),
    ("больше или равно", "num_greater_eq"),
    ("меньше", "num_less"),
    ("меньше или равно", "num_less_eq"),
]

COMMON_OPERATORS = [
    ("имеет значение", "has_value"),
    ("не имеет значения", "has_no_value"),
]

# =================== Parameter info wrapper ===================


class ParameterInfo(object):
    """Wraps a parameter ElementId with its display name and storage type."""

    def __init__(self, name, param_id, storage_type="string"):
        self.name = name
        self.param_id = param_id
        self.storage_type = storage_type

    def __str__(self):
        return self.name


class OperatorInfo(object):
    """Wraps operator display name and internal key."""

    def __init__(self, display_name, key):
        self.display_name = display_name
        self.key = key

    def __str__(self):
        return self.display_name


# =================== Data models ===================


class CategoryCheckItem(INotifyPropertyChanged):
    """Category checkbox item for the editor."""

    def __init__(self, name, category_id, is_checked=False):
        self._name = name
        self._category_id = category_id
        self._is_checked = is_checked
        self._propertyChanged = None

    @property
    def Name(self):
        return self._name

    @property
    def CategoryId(self):
        return self._category_id

    @property
    def IsChecked(self):
        return self._is_checked

    @IsChecked.setter
    def IsChecked(self, value):
        if self._is_checked != value:
            self._is_checked = value
            self._raise("IsChecked")

    def add_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Combine(self._propertyChanged, handler)

    def remove_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Remove(self._propertyChanged, handler)

    def _raise(self, prop):
        if self._propertyChanged:
            self._propertyChanged(self, PropertyChangedEventArgs(prop))


class RuleItem(INotifyPropertyChanged):
    """Single filter rule in the editor."""

    def __init__(
        self,
        param_info=None,
        operator_info=None,
        value="",
        available_params=None,
        param_type="string",
    ):
        self._selected_parameter = param_info
        self._selected_operator = operator_info
        self._value = value
        self._param_type = param_type
        self._available_params = available_params or []
        self._available_operators = self._build_operators(param_type)
        self._propertyChanged = None

    def _build_operators(self, param_type):
        """Build operator list based on parameter type."""
        ops = []
        if param_type == "element_id":
            ops.append(OperatorInfo("равно", "eid_equals"))
            ops.append(OperatorInfo("не равно", "eid_not_equals"))
        elif param_type == "string":
            for name, key in STRING_OPERATORS:
                ops.append(OperatorInfo(name, key))
        else:
            for name, key in NUMERIC_OPERATORS:
                ops.append(OperatorInfo(name, key))

        for name, key in COMMON_OPERATORS:
            ops.append(OperatorInfo(name, key))
        return ops

    @property
    def SelectedParameter(self):
        return self._selected_parameter

    @SelectedParameter.setter
    def SelectedParameter(self, value):
        if self._selected_parameter != value:
            self._selected_parameter = value

            if value:
                new_type = value.storage_type

                if new_type != self._param_type:
                    self._param_type = new_type
                    self._available_operators = self._build_operators(new_type)
                    self._raise("AvailableOperators")

                    # Reset operator
                    if self._available_operators:
                        self._selected_operator = self._available_operators[0]
                        self._raise("SelectedOperator")

            self._raise("SelectedParameter")

    @property
    def SelectedOperator(self):
        return self._selected_operator

    @SelectedOperator.setter
    def SelectedOperator(self, value):
        if self._selected_operator != value:
            self._selected_operator = value
            self._raise("SelectedOperator")
            self._raise("IsValueVisible")

    @property
    def Value(self):
        return self._value

    @Value.setter
    def Value(self, value):
        if self._value != value:
            self._value = value
            self._raise("Value")

    @property
    def AvailableParameters(self):
        return self._available_params

    @property
    def AvailableOperators(self):
        return self._available_operators

    @property
    def IsValueVisible(self):
        if not self._selected_operator:
            return True
        return self._selected_operator.key not in ("has_value", "has_no_value")

    def add_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Combine(self._propertyChanged, handler)

    def remove_PropertyChanged(self, handler):
        self._propertyChanged = EventHandler.Remove(self._propertyChanged, handler)

    def _raise(self, prop):
        if self._propertyChanged:
            self._propertyChanged(self, PropertyChangedEventArgs(prop))


# =================== Rule parsing ===================


def _get_param_name(doc, param_id):
    """Get parameter display name from ElementId."""
    # BuiltInParameter
    int_val = param_id.IntegerValue
    if int_val < 0:
        try:
            bip = BuiltInParameter(int_val)
            return LabelUtils.GetLabelFor(bip)
        except:
            return "Параметр [{}]".format(int_val)

    # SharedParameter or project parameter
    elem = doc.GetElement(param_id)
    if elem:
        return elem.Name

    return "Параметр [{}]".format(int_val)


def _get_storage_type(rule):
    """Determine storage type from rule class."""
    if isinstance(rule, FilterStringRule):
        return "string"
    if isinstance(rule, (FilterDoubleRule, FilterIntegerRule)):
        return "number"
    if isinstance(rule, FilterElementIdRule):
        return "element_id"
    return "string"


def _identify_operator(rule):
    """Parse a FilterRule into an OperatorInfo key."""
    if isinstance(rule, HasNoValueFilterRule):
        return "has_no_value"
    if isinstance(rule, HasValueFilterRule):
        return "has_value"

    # Check for inverse wrapper
    is_inverse = isinstance(rule, FilterInverseRule)
    inner_rule = rule.GetInnerRule() if is_inverse else rule

    if isinstance(inner_rule, FilterStringRule):
        evaluator = inner_rule.GetEvaluator()
        ev_type = type(evaluator).__name__
        mapping = {
            "FilterStringEquals": "str_equals",
            "FilterStringContains": "str_contains",
            "FilterStringBeginsWith": "str_begins",
            "FilterStringEndsWith": "str_ends",
        }
        key = mapping.get(ev_type, "str_equals")

        if is_inverse:
            inverse_map = {
                "str_equals": "str_not_equals",
                "str_contains": "str_not_contains",
            }
            key = inverse_map.get(key, key)

        return key

    if isinstance(inner_rule, FilterElementIdRule):
        if is_inverse:
            return "eid_not_equals"
        return "eid_equals"

    if isinstance(inner_rule, (FilterDoubleRule, FilterIntegerRule)):
        evaluator = inner_rule.GetEvaluator()
        ev_type = type(evaluator).__name__
        mapping = {
            "FilterNumericEquals": "num_equals",
            "FilterNumericGreater": "num_greater",
            "FilterNumericGreaterOrEqual": "num_greater_eq",
            "FilterNumericLess": "num_less",
            "FilterNumericLessOrEqual": "num_less_eq",
        }
        key = mapping.get(ev_type, "num_equals")

        if is_inverse and key == "num_equals":
            key = "num_not_equals"

        return key

    return "str_equals"


def _get_rule_value(rule, doc=None):
    """Extract the value from a FilterRule as string."""
    if isinstance(rule, (HasNoValueFilterRule, HasValueFilterRule)):
        return ""

    inner = rule.GetInnerRule() if isinstance(rule, FilterInverseRule) else rule

    if isinstance(inner, FilterStringRule):
        return inner.RuleString or ""

    if isinstance(inner, FilterDoubleRule):
        return str(inner.RuleValue)

    if isinstance(inner, FilterIntegerRule):
        return str(inner.RuleValue)

    if isinstance(inner, FilterElementIdRule):
        return _resolve_element_name(doc, inner.RuleValue)

    return ""


def _resolve_element_name(doc, elem_id):
    """Resolve ElementId to element name."""
    if not doc or not elem_id or elem_id == ElementId.InvalidElementId:
        return str(elem_id.IntegerValue) if elem_id else ""

    elem = doc.GetElement(elem_id)
    if not elem:
        return str(elem_id.IntegerValue)

    name = getattr(elem, "Name", None)

    return name if name else str(elem_id.IntegerValue)


def _get_rule_param_id(rule):
    """Get parameter ElementId from rule."""
    if isinstance(rule, (HasNoValueFilterRule, HasValueFilterRule)):
        return rule.GetRuleParameter()

    inner = rule.GetInnerRule() if isinstance(rule, FilterInverseRule) else rule

    return inner.GetRuleParameter()


def parse_element_filter(doc, pfe):
    """Parse ParameterFilterElement into (logic_type, list_of_rule_dicts).

    Returns:
        (str, list): ("and"|"or"|"unknown", [{"param_id", "param_name", "operator_key", "value", "storage_type"}])
        None if filter is not supported.
    """
    elem_filter = pfe.GetElementFilter()
    if elem_filter is None:
        # Empty filter (no rules yet) — valid, not unsupported
        return ("and", [])

    rules_data = []
    logic = "and"

    if isinstance(elem_filter, ElementParameterFilter):
        rules_data = _parse_param_filter(doc, elem_filter)
    elif isinstance(elem_filter, LogicalAndFilter):
        logic = "and"

        for sub in elem_filter.GetFilters():
            if isinstance(sub, ElementParameterFilter):
                rules_data.extend(_parse_param_filter(doc, sub))
            else:
                return None  # nested logic not supported
    elif isinstance(elem_filter, LogicalOrFilter):
        logic = "or"

        for sub in elem_filter.GetFilters():
            if isinstance(sub, ElementParameterFilter):
                rules_data.extend(_parse_param_filter(doc, sub))
            else:
                return None
    else:
        return None

    return (logic, rules_data)


def _parse_param_filter(doc, epf):
    """Parse ElementParameterFilter into list of rule dicts."""
    results = []
    for rule in epf.GetRules():
        param_id = _get_rule_param_id(rule)
        results.append(
            {
                "param_id": param_id,
                "param_name": _get_param_name(doc, param_id),
                "operator_key": _identify_operator(rule),
                "value": _get_rule_value(rule, doc),
                "storage_type": _get_storage_type(rule),
            }
        )
    return results


# =================== Rule building ===================


def _create_evaluator(key):
    """Create evaluator from operator key."""
    mapping = {
        "str_equals": FilterStringEquals(),
        "str_contains": FilterStringContains(),
        "str_begins": FilterStringBeginsWith(),
        "str_ends": FilterStringEndsWith(),
        "num_equals": FilterNumericEquals(),
        "num_greater": FilterNumericGreater(),
        "num_greater_eq": FilterNumericGreaterOrEqual(),
        "num_less": FilterNumericLess(),
        "num_less_eq": FilterNumericLessOrEqual(),
    }
    return mapping.get(key)


def _find_element_by_name(doc, name):
    """Find ElementId by element name. Returns InvalidElementId if not found."""
    if not doc or not name:
        return ElementId.InvalidElementId
    # Try parsing as integer ID first (fallback)
    try:
        int_id = int(name)
        return ElementId(int_id)
    except (ValueError, TypeError):
        pass

    collector = FilteredElementCollector(doc).WhereElementIsNotElementType()
    for elem in collector:
        if getattr(elem, "Name", None) == name:
            return elem.Id

    # Also check element types
    collector_t = FilteredElementCollector(doc).WhereElementIsElementType()
    for elem in collector_t:
        if getattr(elem, "Name", None) == name:
            return elem.Id

    return ElementId.InvalidElementId


def _build_single_rule(rule_item, doc=None):
    """Build a FilterRule from a RuleItem."""
    key = rule_item.SelectedOperator.key
    param_id = rule_item.SelectedParameter.param_id
    provider = ParameterValueProvider(param_id)
    value = rule_item.Value or ""

    if key == "has_value":
        return HasValueFilterRule(param_id)
    if key == "has_no_value":
        return HasNoValueFilterRule(param_id)

    # ElementId rules
    if key in ("eid_equals", "eid_not_equals"):
        eid = _find_element_by_name(doc, value)
        inner = FilterElementIdRule(provider, FilterNumericEquals(), eid)

        if key == "eid_not_equals":
            return FilterInverseRule(inner)
        return inner

    # Inverse string operators
    if key == "str_not_equals":
        evaluator = FilterStringEquals()
        inner = FilterStringRule(provider, evaluator, value)

        return FilterInverseRule(inner)

    if key == "str_not_contains":
        evaluator = FilterStringContains()
        inner = FilterStringRule(provider, evaluator, value)

        return FilterInverseRule(inner)

    # Inverse numeric
    if key == "num_not_equals":
        evaluator = FilterNumericEquals()
        num_val = _parse_number(value)
        inner = FilterDoubleRule(provider, evaluator, num_val, 1e-6)

        return FilterInverseRule(inner)

    evaluator = _create_evaluator(key)
    if not evaluator:
        return None

    # String rules
    if key.startswith("str_"):
        return FilterStringRule(provider, evaluator, value)

    # Numeric rules
    num_val = _parse_number(value)
    return FilterDoubleRule(provider, evaluator, num_val, 1e-6)


def _parse_number(value):
    """Parse string to float, default 0."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def build_element_filter(rule_items, is_and, doc=None):
    """Build ElementFilter from list of RuleItems.

    Args:
        rule_items: list of RuleItem
        is_and: True for AND, False for OR
        doc: Revit Document (needed for ElementId rules)

    Returns:
        ElementFilter or None
    """
    if not rule_items:
        return None

    filters = []
    for ri in rule_items:
        if not ri.SelectedParameter or not ri.SelectedOperator:
            continue

        rule = _build_single_rule(ri, doc)
        if rule:
            filters.append(ElementParameterFilter(rule))

    if not filters:
        return None

    if len(filters) == 1:
        return filters[0]

    if is_and:
        return LogicalAndFilter(filters)

    return LogicalOrFilter(filters)


# =================== Available parameters ===================


def get_filterable_parameters(doc, category_ids):
    """Get list of ParameterInfo for categories."""
    params = []
    try:
        cat_list = List[ElementId](category_ids)
        param_ids = ParameterFilterUtilities.GetFilterableParametersInCommon(
            doc, cat_list
        )

        for pid in param_ids:
            name = _get_param_name(doc, pid)
            # Determine type heuristically
            storage = "string"
            int_val = pid.IntegerValue

            if int_val < 0:
                try:
                    bip = BuiltInParameter(int_val)
                    # Numeric parameters heuristic by name
                    label = name.lower()
                    numeric_hints = [
                        "height",
                        "width",
                        "length",
                        "area",
                        "volume",
                        "offset",
                        "толщина",
                        "высота",
                        "ширина",
                        "длина",
                        "площадь",
                        "объем",
                        "смещение",
                        "отметка",
                    ]

                    if any(h in label for h in numeric_hints):
                        storage = "number"
                except:
                    pass

            params.append(ParameterInfo(name, pid, storage))
    except:
        print(traceback.format_exc())

    params.sort(key=lambda p: p.name)
    return params


# =================== XAML ===================

EDITOR_XAML = """
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Настройки фильтра"
        Width="700" Height="550"
        WindowStartupLocation="CenterScreen"
        Background="#F5F5F5">
    <Window.Resources>
        <BooleanToVisibilityConverter x:Key="BoolToVis"/>
    </Window.Resources>

    <Grid Margin="12">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="200" MinHeight="80"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <!-- Filter name -->
        <Grid Grid.Row="0" Margin="0,0,0,10">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="Auto"/>
                <ColumnDefinition Width="*"/>
            </Grid.ColumnDefinitions>

            <TextBlock Grid.Column="0"
               Text="Имя фильтра"
                FontSize="12" FontWeight="SemiBold" Foreground="#666"
                VerticalAlignment="Center"
               Margin="0,0,8,0"/>

            <TextBox x:Name="FilterNameBox" Grid.Column="1"
            FontSize="11" FontWeight="SemiBold"
            Foreground="#2D2D30"
            Background="White"
            BorderBrush="#CCC" BorderThickness="1"
            VerticalContentAlignment="Center"
            Padding="4"/>
        </Grid>

        <!-- Categories section -->
        <Grid Grid.Row="1" Margin="0,0,0,4">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="Auto"/>
                <ColumnDefinition Width="*"/>
            </Grid.ColumnDefinitions>
            <TextBlock Grid.Column="0" Text="Категории"
                       FontSize="12" FontWeight="SemiBold" Foreground="#666"
                       VerticalAlignment="Center"/>
            <TextBox x:Name="CategorySearch" Grid.Column="1"
                     FontSize="11" Margin="24,0,0,0" Height="22"
                     VerticalContentAlignment="Center" Padding="4,0"
                     Foreground="#333" Background="White"
                     BorderBrush="#CCC" BorderThickness="1"/>
        </Grid>

        <Border Grid.Row="2" BorderBrush="#CCC" BorderThickness="1"
                CornerRadius="3" Padding="8" Margin="0,0,0,0"
                Background="White">
            <ScrollViewer VerticalScrollBarVisibility="Auto"
                          HorizontalScrollBarVisibility="Disabled">
                <StackPanel x:Name="CategoriesPanel" Orientation="Vertical"/>
            </ScrollViewer>
        </Border>

        <!-- GridSplitter -->
        <GridSplitter Grid.Row="3" Height="5" HorizontalAlignment="Stretch"
                      VerticalAlignment="Center" Background="Transparent"
                      Cursor="SizeNS" Margin="0,2"/>

        <!-- Conditions header -->
        <Grid Grid.Row="4" Margin="0,0,0,6">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="Auto"/>
                <ColumnDefinition Width="Auto"/>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="Auto"/>
            </Grid.ColumnDefinitions>

            <TextBlock Grid.Column="0" Text="Условия"
                       FontSize="12" FontWeight="SemiBold" Foreground="#666"
                       VerticalAlignment="Center" Margin="0,0,15,0"/>

            <StackPanel Grid.Column="1" Orientation="Horizontal" VerticalAlignment="Center">
                <TextBlock Text="Логика:" Foreground="#666" FontSize="11"
                           VerticalAlignment="Center" Margin="0,0,6,0"/>
                <RadioButton x:Name="RadioAnd" Content="И" GroupName="Logic"
                             IsChecked="True" Margin="0,0,10,0" FontSize="11"/>
                <RadioButton x:Name="RadioOr" Content="ИЛИ" GroupName="Logic"
                             FontSize="11"/>
            </StackPanel>

            <Button x:Name="BtnAddRule" Grid.Column="3"
                    Content="+ Добавить условие"
                    Background="#5F9EA0" Foreground="White"
                    BorderThickness="0" Padding="10,3" FontSize="11"
                    Cursor="Hand"/>
        </Grid>

        <!-- Rules list -->
        <Border Grid.Row="5" BorderBrush="#CCC" BorderThickness="1"
                CornerRadius="3" Background="White" Padding="4">
            <ScrollViewer VerticalScrollBarVisibility="Auto">
                <StackPanel x:Name="RulesPanel"/>
            </ScrollViewer>
        </Border>

        <!-- Warning -->
        <TextBlock x:Name="WarningText" Grid.Row="6"
                   Foreground="#CC0000" FontSize="10" Margin="0,6,0,0"
                   TextWrapping="Wrap" Visibility="Collapsed"/>

        <!-- Buttons -->
        <StackPanel Grid.Row="7" Orientation="Horizontal"
                    HorizontalAlignment="Right" Margin="0,12,0,0">
            <Button x:Name="BtnSave" Content="Сохранить"
                    Width="100" Height="28" Margin="0,0,8,0"
                    Background="#5F9EA0" Foreground="White"
                    BorderThickness="0" FontSize="12" Cursor="Hand"/>
            <Button x:Name="BtnCancel" Content="Отмена"
                    Width="100" Height="28"
                    Background="#DDD" Foreground="#333"
                    BorderThickness="0" FontSize="12" Cursor="Hand"/>
        </StackPanel>
    </Grid>
</Window>
"""

RULE_ROW_XAML = """
<Grid xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
      xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
      Margin="2,3">
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width="45"/>
        <ColumnDefinition Width="*"/>
        <ColumnDefinition Width="140"/>
        <ColumnDefinition Width="250"/>
        <ColumnDefinition Width="28"/>
    </Grid.ColumnDefinitions>

    <TextBlock x:Name="PrefixText" Grid.Column="0"
               FontSize="11" FontWeight="SemiBold"
               Foreground="#5F9EA0" VerticalAlignment="Center"/>

    <ComboBox x:Name="ParamCombo" Grid.Column="1"
            IsEditable="True"
            IsTextSearchEnabled="False"
            StaysOpenOnEdit="True"
            IsTextSearchCaseSensitive="False"
            FontSize="11" Margin="0,0,4,0" Height="24"/>

    <ComboBox x:Name="OperatorCombo" Grid.Column="2"
              FontSize="11" Margin="0,0,4,0" Height="24"/>

    <TextBox x:Name="ValueBox" Grid.Column="3"
             FontSize="11" Margin="0,0,4,0" Height="24"
             VerticalContentAlignment="Center"/>

    <Button x:Name="BtnRemove" Grid.Column="4"
            Content="x" FontSize="11"
            Background="Transparent" BorderThickness="0"
            Foreground="#CC0000" Cursor="Hand"
            Width="24" Height="24"/>
</Grid>
"""


# =================== Editor window ===================


def show_editor(doc, filter_element):
    """Show the filter rules editor window.

    Args:
        doc: Revit Document
        filter_element: ParameterFilterElement

    Returns:
        True if saved, False if cancelled.
    """
    parsed = parse_element_filter(doc, filter_element)

    # Get current categories
    current_cat_ids = list(filter_element.GetCategories())

    # Get all filterable categories
    all_cat_ids = ParameterFilterUtilities.GetAllFilterableCategories()
    all_categories = []

    for cid in all_cat_ids:
        cat = Category.GetCategory(doc, cid)

        if cat:
            is_checked = cid in current_cat_ids
            all_categories.append(CategoryCheckItem(cat.Name, cid, is_checked))

    all_categories.sort(key=lambda c: c.Name)

    # Available parameters (union across selected categories)
    cat_params_cache = {}
    if current_cat_ids:
        available_params = _get_params_union(doc, current_cat_ids, cat_params_cache)
    else:
        available_params = []

    # Parse existing rules
    is_read_only = False
    logic = "and"
    rule_items = []

    if parsed is None:
        is_read_only = True
    else:
        logic, rules_data = parsed

        for rd in rules_data:
            param_info = _find_param(available_params, rd["param_id"], rd["param_name"])
            op_key = rd["operator_key"]
            st = rd["storage_type"]
            ri = RuleItem(
                param_info=param_info,
                value=rd["value"],
                available_params=available_params,
                param_type=st,
            )

            # Find matching operator
            for op in ri.AvailableOperators:
                if op.key == op_key:
                    ri._selected_operator = op
                    break
            rule_items.append(ri)

    # Build window
    window = WPFWindow(EDITOR_XAML, literal_string=True)
    window.FilterNameBox.Text = filter_element.Name

    # Mutable containers
    params_ref = [available_params]
    rule_rows = []

    # Categories
    _populate_categories(
        window, all_categories, doc, params_ref, rule_rows, cat_params_cache
    )

    # Logic radio
    if logic == "or":
        window.RadioOr.IsChecked = True
    else:
        window.RadioAnd.IsChecked = True

    # Rules
    for ri in rule_items:
        _add_rule_row(window, rule_rows, ri, available_params, doc, cat_params_cache)

    if not rule_items and not is_read_only:
        ri = RuleItem(available_params=available_params)
        if available_params:
            ri._selected_parameter = available_params[0]
        if ri.AvailableOperators:
            ri._selected_operator = ri.AvailableOperators[0]
        _add_rule_row(window, rule_rows, ri, available_params, doc, cat_params_cache)

    # Initial category availability check
    _refresh_category_availability(window, doc, rule_rows, cat_params_cache)

    # Read-only warning
    if is_read_only:
        window.WarningText.Text = (
            "Этот тип фильтра не поддерживается для редактирования."
        )
        window.WarningText.Visibility = System.Windows.Visibility.Visible
        window.BtnSave.IsEnabled = False
        window.BtnAddRule.IsEnabled = False

    # Events
    result = [False]

    def on_add_rule(s, e):
        ap = params_ref[0]
        ri = RuleItem(available_params=ap)

        if ap:
            ri._selected_parameter = ap[0]

        if ri.AvailableOperators:
            ri._selected_operator = ri.AvailableOperators[0]

        _add_rule_row(window, rule_rows, ri, ap, doc, cat_params_cache)

    def on_save(s, e):
        conflict = _pre_save_validate(doc, window, rule_rows, cat_params_cache)

        if conflict:
            forms.alert(conflict)
            return

        result[0] = True
        window.Close()

    def on_cancel(s, e):
        window.Close()

    def on_category_search(s, e):
        _filter_categories(window, s.Text)

    def on_logic_changed(s, e):
        _update_prefixes(window, rule_rows)

    window.BtnAddRule.Click += on_add_rule
    window.BtnSave.Click += on_save
    window.BtnCancel.Click += on_cancel
    window.CategorySearch.TextChanged += on_category_search
    window.RadioAnd.Checked += on_logic_changed
    window.RadioOr.Checked += on_logic_changed

    window.ShowDialog()

    if not result[0]:
        return False

    # Collect data and save
    return _save_filter(
        doc, filter_element, window, all_categories, rule_rows, cat_params_cache
    )


def _find_param(available_params, param_id, fallback_name):
    """Find ParameterInfo by id, or create a fallback."""
    for p in available_params:
        if p.param_id == param_id:
            return p
    return ParameterInfo(fallback_name, param_id)


def _iter_category_checkboxes(window):
    """Iterate all category CheckBox widgets from the nested group structure.

    CategoriesPanel is a StackPanel of group StackPanels.
    Each group contains: TextBlock header, Separator, WrapPanel of CheckBoxes.
    """
    for group_panel in window.CategoriesPanel.Children:
        # group_panel is a StackPanel; its last child is the WrapPanel with checkboxes
        if not hasattr(group_panel, "Children"):
            continue
        for child in group_panel.Children:
            if not hasattr(child, "Children"):
                continue
            # This is the WrapPanel
            for cb in child.Children:
                tag = getattr(cb, "Tag", None)
                if tag and hasattr(tag, "CategoryId"):
                    yield cb


def _filter_categories(window, search_text):
    """Show/hide category checkboxes and letter groups based on search text."""
    query = (search_text or "").lower().strip()

    for group_panel in window.CategoriesPanel.Children:
        if not hasattr(group_panel, "Children"):
            continue

        any_visible = False
        for child in group_panel.Children:
            if not hasattr(child, "Children"):
                continue
            # WrapPanel of checkboxes
            for cb in child.Children:
                tag = getattr(cb, "Tag", None)
                if not tag or not hasattr(tag, "Name"):
                    continue
                if not query or query in tag.Name.lower():
                    cb.Visibility = WinNS.Visibility.Visible
                    any_visible = True
                else:
                    cb.Visibility = WinNS.Visibility.Collapsed

        # Hide entire group if no checkboxes visible
        if query:
            group_panel.Visibility = (
                WinNS.Visibility.Visible if any_visible else WinNS.Visibility.Collapsed
            )
        else:
            group_panel.Visibility = WinNS.Visibility.Visible


def _get_cat_param_ids(doc, cat_id, cache):
    """Get parameter id set for a category (lazy cached)."""
    key = cat_id.IntegerValue

    if key not in cache:
        params = get_filterable_parameters(doc, [cat_id])
        cache[key] = set(p.param_id.IntegerValue for p in params)

    return cache[key]


def _get_params_union(doc, category_ids, cache):
    """Get union of parameters across all categories."""
    seen = {}
    for cid in category_ids:
        params = get_filterable_parameters(doc, [cid])
        cache[cid.IntegerValue] = set(p.param_id.IntegerValue for p in params)

        for p in params:
            pid_key = p.param_id.IntegerValue
            if pid_key not in seen:
                seen[pid_key] = p

    return sorted(seen.values(), key=lambda p: p.name)


def _populate_categories(window, categories, doc, params_ref, rule_rows, cache):
    """Add category checkboxes grouped by first letter."""

    panel = window.CategoriesPanel
    panel.Children.Clear()

    # Group by first letter
    groups = {}
    for cat_item in categories:
        first_letter = cat_item.Name[0].upper() if cat_item.Name else "#"
        groups.setdefault(first_letter, []).append(cat_item)

    for letter in sorted(groups.keys()):
        # Group container (vertical StackPanel: header + wrap of checkboxes)
        group_panel = Controls.StackPanel()
        group_panel.Orientation = Controls.Orientation.Vertical
        group_panel.Margin = WinNS.Thickness(0, 2, 0, 4)
        group_panel.Tag = letter  # tag with letter for search filtering

        # Letter header
        header = Controls.TextBlock()
        header.Text = letter
        header.FontWeight = WinNS.FontWeights.SemiBold
        header.FontSize = 12
        header.Foreground = WinNS.Media.Brushes.Gray
        header.Margin = WinNS.Thickness(0, 2, 0, 2)
        group_panel.Children.Add(header)

        # Separator
        separator = Controls.Separator()
        separator.Margin = WinNS.Thickness(0, 0, 0, 4)
        group_panel.Children.Add(separator)

        # WrapPanel for checkboxes in this group
        wrap = Controls.WrapPanel()
        wrap.Orientation = Controls.Orientation.Horizontal

        for cat_item in sorted(groups[letter], key=lambda c: c.Name):
            cb = Controls.CheckBox()
            cb.Content = cat_item.Name
            cb.IsChecked = cat_item.IsChecked
            cb.Tag = cat_item
            cb.Margin = WinNS.Thickness(0, 2, 12, 2)
            cb.FontSize = 11

            def make_handler(ci):
                def handler(s, e):
                    ci.IsChecked = s.IsChecked
                    _on_categories_changed(
                        window, categories, doc, params_ref, rule_rows, cache
                    )

                return handler

            cb.Checked += make_handler(cat_item)
            cb.Unchecked += make_handler(cat_item)

            wrap.Children.Add(cb)

        group_panel.Children.Add(wrap)
        panel.Children.Add(group_panel)


def _on_categories_changed(window, categories, doc, params_ref, rule_rows, cache):
    """Refresh available parameters (union) when categories change."""
    checked_ids = [c.CategoryId for c in categories if c.IsChecked]

    if checked_ids:
        new_params = _get_params_union(doc, checked_ids, cache)
    else:
        new_params = []

    params_ref[0] = new_params

    for ri, grid in rule_rows:
        param_combo = grid.FindName("ParamCombo")
        if not param_combo:
            continue

        old_param = param_combo.SelectedItem

        param_combo.ItemsSource = None
        param_combo.ItemsSource = list(new_params)
        param_combo.DisplayMemberPath = "name"

        if old_param:
            for p in new_params:
                if p.param_id == old_param.param_id:
                    param_combo.SelectedItem = p
                    break

        ri._available_params = new_params

    _refresh_category_availability(window, doc, rule_rows, cache)


def _refresh_category_availability(window, doc, rule_rows, cache):
    """Disable categories that lack parameters used in current rules."""
    used_pids = set()
    used_names = {}

    for ri, grid in rule_rows:
        param_combo = grid.FindName("ParamCombo")
        if not param_combo:
            continue

        p = param_combo.SelectedItem
        if not p:
            continue

        pid_int = p.param_id.IntegerValue
        used_pids.add(pid_int)
        used_names[pid_int] = p.name

    for child in _iter_category_checkboxes(window):
        tag = child.Tag
        cat_id = tag.CategoryId
        cat_pids = _get_cat_param_ids(doc, cat_id, cache)

        if not used_pids:
            child.IsEnabled = True
            child.ToolTip = None
            continue

        missing = used_pids - cat_pids

        if missing:
            names = [used_names[m] for m in missing if m in used_names]
            child.IsEnabled = False
            child.ToolTip = "Нет параметра: {}".format(", ".join(names))
        else:
            child.IsEnabled = True
            child.ToolTip = None


from System.Windows.Data import CollectionViewSource


def _add_rule_row(window, rule_rows, rule_item, available_params, doc=None, cache=None):
    """Add a rule row with stable substring search using CollectionView."""

    grid = XamlReader.Load(XmlReader.Create(StringReader(RULE_ROW_XAML)))

    prefix_text = grid.FindName("PrefixText")
    param_combo = grid.FindName("ParamCombo")
    operator_combo = grid.FindName("OperatorCombo")
    value_box = grid.FindName("ValueBox")
    btn_remove = grid.FindName("BtnRemove")

    # ---------- Prefix ----------
    idx = len(rule_rows)
    is_and = window.RadioAnd.IsChecked
    conjunction = "И" if is_and else "ИЛИ"
    prefix_text.Text = "ЕСЛИ" if idx == 0 else conjunction

    # ---------- Parameters ----------
    all_params = list(available_params)
    param_combo.ItemsSource = all_params
    param_combo.DisplayMemberPath = "name"
    param_combo.IsTextSearchEnabled = False

    view = CollectionViewSource.GetDefaultView(param_combo.ItemsSource)

    initializing = [True]

    def filter_func(item):
        if initializing[0]:
            return True
        text = (param_combo.Text or "").lower()
        if not text:
            return True
        return text in item.name.lower()

    view.Filter = lambda item: filter_func(item)

    def on_text_changed(sender, args):
        if initializing[0]:
            return
        view.Refresh()
        param_combo.IsDropDownOpen = True

    param_combo.ApplyTemplate()
    editable_tb = param_combo.Template.FindName("PART_EditableTextBox", param_combo)

    if editable_tb:
        editable_tb.TextChanged += on_text_changed

    if rule_item.SelectedParameter:
        param_combo.SelectedItem = rule_item.SelectedParameter

    initializing[0] = False

    # ---------- Operators ----------
    operators = list(rule_item.AvailableOperators)
    operator_combo.ItemsSource = operators
    operator_combo.DisplayMemberPath = "display_name"

    if rule_item.SelectedOperator:
        operator_combo.SelectedItem = rule_item.SelectedOperator

    # ---------- Value ----------
    value_box.Text = rule_item.Value or ""

    if not rule_item.IsValueVisible:
        value_box.IsEnabled = False
        value_box.Text = ""

    # ---------- Events ----------

    def on_param_changed(s, e):
        sel = param_combo.SelectedItem
        if not sel:
            return

        rule_item.SelectedParameter = sel

        new_ops = list(rule_item.AvailableOperators)
        operator_combo.ItemsSource = new_ops
        operator_combo.DisplayMemberPath = "display_name"

        if new_ops:
            operator_combo.SelectedIndex = 0

        if cache is not None:
            _refresh_category_availability(window, doc, rule_rows, cache)

    def on_operator_changed(s, e):
        sel = operator_combo.SelectedItem
        if not sel:
            return

        rule_item.SelectedOperator = sel

        no_value = sel.key in ("has_value", "has_no_value")
        value_box.IsEnabled = not no_value

        if no_value:
            value_box.Text = ""

    def on_value_changed(s, e):
        rule_item.Value = value_box.Text

    param_combo.SelectionChanged += on_param_changed
    operator_combo.SelectionChanged += on_operator_changed
    value_box.TextChanged += on_value_changed

    # ---------- Remove ----------
    entry = (rule_item, grid)
    rule_rows.append(entry)

    def on_remove(s, e):
        if entry in rule_rows:
            rule_rows.remove(entry)
            window.RulesPanel.Children.Remove(grid)
            _update_prefixes(window, rule_rows)

            if cache is not None:
                _refresh_category_availability(window, doc, rule_rows, cache)

    btn_remove.Click += on_remove

    window.RulesPanel.Children.Add(grid)


def _update_prefixes(window, rule_rows):
    """Update ЕСЛИ/И/ИЛИ prefixes based on logic mode."""
    is_and = window.RadioAnd.IsChecked
    conjunction = "И" if is_and else "ИЛИ"

    for i, (ri, grid) in enumerate(rule_rows):
        prefix = grid.FindName("PrefixText")
        if prefix:
            prefix.Text = "ЕСЛИ" if i == 0 else conjunction


def _pre_save_validate(doc, window, rule_rows, cache):
    cat_ids = []
    for child in _iter_category_checkboxes(window):
        if child.IsChecked:
            cat_ids.append(child.Tag.CategoryId)

    if not cat_ids:
        return "Не выбрана ни одна категория."

    rule_items = []

    for ri, grid in rule_rows:
        param_combo = grid.FindName("ParamCombo")
        operator_combo = grid.FindName("OperatorCombo")

        if param_combo and param_combo.SelectedItem:
            ri._selected_parameter = param_combo.SelectedItem

        if operator_combo and operator_combo.SelectedItem:
            ri._selected_operator = operator_combo.SelectedItem

        rule_items.append(ri)

    return _validate_rules_vs_categories(doc, cat_ids, rule_items, cache)


def _save_filter(doc, filter_element, window, all_categories, rule_rows, cache=None):
    """Save changes to the filter element."""
    try:
        # Collect selected categories
        new_cat_ids = []
        for child in _iter_category_checkboxes(window):
            if child.IsChecked:
                new_cat_ids.append(child.Tag.CategoryId)

        if not new_cat_ids:
            return False

        # Sync values from UI
        rule_items = []
        for ri, grid in rule_rows:
            value_box = grid.FindName("ValueBox")
            param_combo = grid.FindName("ParamCombo")
            operator_combo = grid.FindName("OperatorCombo")

            if value_box:
                ri.Value = value_box.Text

            if param_combo and param_combo.SelectedItem:
                ri._selected_parameter = param_combo.SelectedItem

            if operator_combo and operator_combo.SelectedItem:
                ri._selected_operator = operator_combo.SelectedItem

            rule_items.append(ri)

        is_and = window.RadioAnd.IsChecked
        new_filter = build_element_filter(rule_items, is_and, doc)

        cat_list = List[ElementId]()
        for cid in new_cat_ids:
            cat_list.Add(cid)

        with Transaction(doc, "Panel_Изменить правила фильтра") as t:
            t.Start()

            new_name = window.FilterNameBox.Text.strip()
            if new_name and new_name != filter_element.Name:
                filter_element.Name = new_name

            filter_element.SetCategories(cat_list)

            if new_filter:
                filter_element.SetElementFilter(new_filter)

            t.Commit()

        return True
    except:
        print(traceback.format_exc())
        return False


def _validate_rules_vs_categories(doc, cat_ids, rule_items, cache):
    """Check that all rule parameters exist in all selected categories.

    Returns error message string or None if valid.
    """
    if not cache:
        cache = {}
    for ri in rule_items:
        if not ri.SelectedParameter:
            continue

        pid = ri.SelectedParameter.param_id.IntegerValue
        pname = ri.SelectedParameter.name
        for cid in cat_ids:
            cat_pids = _get_cat_param_ids(doc, cid, cache)

            if pid not in cat_pids:
                cat = Category.GetCategory(doc, cid)
                cat_name = cat.Name if cat else str(cid.IntegerValue)

                return 'Категория "{}" не содержит параметр "{}".'.format(
                    cat_name, pname
                )

    return None


# Required import for XamlReader
import System.Xml
