# -*- coding: utf-8 -*-
__title__   = 'Конфи-\nгуратор'
__doc__ = 'Описание: Интерфейс для создания групп помещений'
#==================================================
#IMPORTS
#==================================================
import json
import codecs

from pyrevit import forms
from pyrevit.forms import WPFWindow, TemplateListItem
from config import configs
from System.Windows.Markup import XamlReader
from System.IO import StringReader
from System.Windows.Controls import (
    DataGrid,
    DataGridTextColumn,
    DataGridTemplateColumn
)
from System.Windows.Controls import TabItem, DataGrid
from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Data import Binding
from System.Windows.Controls import DataGridLength
from System.Windows.Markup import XamlReader

from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Controls import DataGridTextColumn
from System.Windows.Data import Binding
from System.Windows.Controls import DataGridLength
from System.Windows import RoutedEventHandler
from System.Windows.Controls import DataGridTemplateColumn, Button
from System.Windows import Thickness
from System.Windows import VerticalAlignment
JSON_PATH = configs.get_groups(fp=True)

XAML = u"""
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Конфигуратор помещений"
        Height="600"
        Width="800"
        WindowStartupLocation="CenterScreen">

  <DockPanel>

    <!-- НИЖНЯЯ ПАНЕЛЬ -->
    <DockPanel DockPanel.Dock="Bottom" 
               Margin="5" 
               LastChildFill="False">
               
    <StackPanel DockPanel.Dock="Left" Orientation="Horizontal">
        <Button Name="AddRowBtn"
                Content="Добавить строку"
                Width="150"
                Margin="5"/>
        <Button Name="AddGroupBtn"
                Content="Добавить группу"
                Width="150"
                Margin="5"/>
    </StackPanel>

      <StackPanel DockPanel.Dock="Right" Orientation="Horizontal">
        <Button Name="OkBtn"
                Content="Подтвердить"
                Width="120"
                Margin="5"/>
        <Button Name="CancelBtn"
                Content="Отмена"
                Width="120"
                Margin="5"/>
      </StackPanel>

    </DockPanel>

    <TabControl Name="Tabs"/>

  </DockPanel>
</Window>
"""


class RoomRow(object):
    def __init__(self, data=None):
        data = data or {}
        self.Name = data.get("Наименование", "")
        self.Coeff = data.get("ADKS_Коэффициент площади", 1.0)
        self.Purpose = data.get("PS_Назначение помещений", "")
        self.Group = data.get("PS_Группа помещений", "")
        self.Priority = data.get("PS_Приоритет в нумерации", 0)

    def to_dict(self):
        d = {
            "Наименование": self.Name,
            "PS_Назначение помещений": self.Purpose,
            "PS_Группа помещений": self.Group,
            "PS_Приоритет в нумерации": int(self.Priority)
        }
        d["ADKS_Коэффициент площади"] = float(self.Coeff)
        return d
    

#=========================================================
#Functions
#=========================================================
def recalculate_priorities(collection):
    for i, row in enumerate(collection):
        row.Priority = i + 1

def load_rooms(path):
    with codecs.open(path, 'r', 'utf-8-sig') as f:
        raw = json.load(f)

    result = {}
    for cat, rows in raw.items():
        result[cat] = [RoomRow(r) for r in rows]
    return result

def create_tab(category, rows):
    tab = TabItem()
    tab.Header = category

    grid = DataGrid()
    grid.AutoGenerateColumns = False
    grid.CanUserAddRows = False
    grid.CanUserDeleteRows = False
    grid.IsReadOnly = False
    grid.VerticalContentAlignment = VerticalAlignment.Stretch

    collection = ObservableCollection[RoomRow]()
    for r in rows:
        collection.Add(r)

    # ---------- MOVE COLUMN ----------
    move_xaml = u"""
<DataTemplate xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation">
  <StackPanel Orientation="Vertical">
    <Button Content="▲" Margin="1" Padding="0,0" Width="22"/>
    <Button Content="▼" Margin="1" Padding="0,0" Width="22"/>
  </StackPanel>
</DataTemplate>
"""
    move_col = DataGridTemplateColumn()
    move_col.Width = DataGridLength(30)
    move_col.CellTemplate = XamlReader.Parse(move_xaml)
    grid.Columns.Add(move_col)

    # ---------- DELETE COLUMN ----------
    delete_xaml = u"""
<DataTemplate xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation">
  <Button Content="✕"
          Margin="2"
          Padding="1,1"
          HorizontalAlignment="Center"
          VerticalAlignment="Center"/>
</DataTemplate>
"""
    delete_col = DataGridTemplateColumn()
    delete_col.Width = DataGridLength(30)
    delete_col.CellTemplate = XamlReader.Parse(delete_xaml)
    grid.Columns.Add(delete_col)

    # ---------- TEXT COLUMNS ----------
    def col(header, path, width):
        c = DataGridTextColumn()
        c.Header = header
        c.Binding = Binding(path)
        c.Width = DataGridLength(width)

        # XAML-стиль для центрирования
        style_xaml = u"""
        <Style xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
            TargetType="TextBlock">
            <Setter Property="HorizontalAlignment" Value="Center"/>
            <Setter Property="VerticalAlignment" Value="Center"/>
            <Setter Property="TextWrapping" Value="Wrap"/>
            <Setter Property="TextAlignment" Value="Center"/>
        </Style>
        """
        c.ElementStyle = XamlReader.Parse(style_xaml)
        return c

    grid.Columns.Add(col(u"Наименование", "Name", 260))
    grid.Columns.Add(col(u"Коэф. площади", "Coeff", 120))
    # grid.Columns.Add(col(u"Назначение", "Purpose", 180))
    grid.Columns.Add(col(u"Группа", "Group", 180))
    grid.Columns.Add(col(u"Приоритет", "Priority", 100))

    grid.ItemsSource = collection
    tab.Content = grid

    # ---------- BUTTON HANDLING ----------

    def on_grid_click(sender, args):
        src = args.OriginalSource
        if not src or src.GetType().Name != "Button":
            return

        row = src.DataContext
        if row not in collection:
            return

        idx = collection.IndexOf(row)

        grid.CommitEdit()
        grid.CommitEdit()

        if src.Content == u"✕":
            collection.Remove(row)

        elif src.Content == u"▲" and idx > 0:
            collection.Move(idx, idx - 1)

        elif src.Content == u"▼" and idx < collection.Count - 1:
            collection.Move(idx, idx + 1)
        
        recalculate_priorities(collection)

        grid.Items.Refresh()

    grid.PreviewMouseLeftButtonUp += on_grid_click
    

    return tab, collection



def collect_result(tabs_data):
    result = {}
    for cat, collection in tabs_data.items():
        result[cat] = [row.to_dict() for row in collection]
    return result


def on_add_group(sender, args):
    # ввод имени группы
    name = forms.ask_for_string(
        default="Жилье",
        prompt="Введите название группы помещений"
    )

    if not name:
        return

    # защита от дублей
    if name in tabs_data:
        forms.alert(u"Группа уже существует", exitscript=False)
        return

    # создаём пустую вкладку
    tab, collection = create_tab(name, [])
    window.Tabs.Items.Add(tab)
    tabs_data[name] = collection

    # делаем активной
    window.Tabs.SelectedItem = tab


def on_add_row(sender, args):
    tab = window.Tabs.SelectedItem
    if not tab:
        return

    grid = tab.Content
    collection = tabs_data.get(tab.Header)
    if collection is None:
        return

    grid.CommitEdit()
    grid.CommitEdit()

    selected = grid.SelectedItem

    new_row = RoomRow()
    new_row.Purpose = tab.Header

    if selected and selected in collection:
        idx = collection.IndexOf(selected)
        collection.Insert(idx + 1, new_row)
    else:
        collection.Add(new_row)

    recalculate_priorities(collection)

    grid.Items.Refresh()

    grid.SelectedItem = new_row
    grid.ScrollIntoView(new_row)

def on_ok(sender, args):
    data = collect_result(tabs_data)
    with codecs.open(JSON_PATH, 'w', 'utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    window.Close()

def on_cancel(sender, args):
    window.Close()

#==================================================
#MAIN
#==================================================
categories = load_rooms(JSON_PATH)

window = WPFWindow(XAML, literal_string=True)
tabs_data = {}

for cat, rows in categories.items():
    tab, collection = create_tab(cat, rows)
    window.Tabs.Items.Add(tab)
    tabs_data[cat] = collection

window.AddRowBtn.Click += on_add_row
window.OkBtn.Click += on_ok
window.CancelBtn.Click += on_cancel
window.AddGroupBtn.Click += on_add_group

window.ShowDialog()