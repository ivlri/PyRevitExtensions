# -*- coding: utf-8 -*-
import json
import codecs
import os
from collections import defaultdict

from pyrevit import forms
from config import configs

from System.Windows.Controls import (
    TabItem,
    Button,
    WrapPanel,
    ScrollViewer,
    GroupBox,
    StackPanel,
    TextBlock,
    ScrollBarVisibility, 
    Viewbox
)
from System.Windows import Thickness, HorizontalAlignment, VerticalAlignment
from System.Windows import TextWrapping, TextAlignment

from pyrevit import forms, revit, HOST_APP
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException
from System.Windows.Media import SolidColorBrush, Colors
# --------------------------------------------------
JSON_PATH = configs.get_groups(fp=True)
XAML_PATH = os.path.join(os.path.dirname(__file__), "RoomsPanel.xaml")
# --------------------------------------------------


def load_rooms(path):
    with codecs.open(path, 'r', 'utf-8-sig') as f:
        raw = json.load(f)

    result = {}
    for cat, rows in raw.items():
        result[cat] = [RoomRow(r) for r in rows]
    return result


class RoomRow(object):
    def __init__(self, data=None):
        data = data or {}
        self.Name = data.get("Наименование", "")
        self.Group = data.get("PS_Группа помещений", u"Без группы")


class CreateRoomHandler(IExternalEventHandler):
    """
    Обработчик для создания помещений
    """

    def __init__(self, panel):
        self.panel = panel
        
    def Execute(self, app):
        doc = HOST_APP.doc
        uidoc = HOST_APP.uidoc
        active_view = doc.ActiveView
        selection = uidoc.Selection 

        rname = self.panel.room_name
        with forms.WarningBar(title="{{{}}} - Выберите точку вставки помещения. Чтобы закончить выбор нажмите ESC".format(rname)):
            with Transaction(doc, 'Rooms_Создание помещений') as t:
                t.Start()
                while True:
                    try:
                        point = selection.PickPoint(ObjectSnapTypes.None)
                        room = doc.Create.NewRoom(active_view.GenLevel, UV(point.X, point.Y))
                        room.Name = rname if rname else ""
                    except OperationCanceledException:
                        break
                t.Commit()

    def GetName(self):
        return "Create Rooms"
    
class RoomsDockablePanel(forms.WPFPanel):
    panel_title = "Помещения"
    panel_id = "a3f8d9e7-5b2c-4f1a-9c6d-8e7b4a2f1c0d"
    panel_source = XAML_PATH

    def __init__(self):
        super(RoomsDockablePanel, self).__init__()
        self._build_ui()

        self.create_room_handler = CreateRoomHandler(self)
        self.create_room_event =  ExternalEvent.Create(self.create_room_handler)

        self.room_name = None
    # ---------------- UI ----------------
    def _build_ui(self):
        categories = load_rooms(JSON_PATH)

        self.Tabs.Items.Clear()

        for cat, rooms in categories.items():
            self.Tabs.Items.Add(self._create_tab_buttons(cat, rooms))

    def _create_tab_buttons(self, category, rooms):
        tab = TabItem()
        tab.Header = category
        tab.Background = SolidColorBrush(Colors.White)

        # группировка по RoomRow.Group
        grouped = defaultdict(list)
        for r in rooms:
            grouped[r.Group or u"Без группы"].append(r)

        root_panel = StackPanel()
        root_panel.Margin = Thickness(10)
        root_panel.Background = SolidColorBrush(Colors.White)

        for group_name in sorted(grouped.keys()):
            group_box = GroupBox()
            group_box.Header = group_name
            group_box.Margin = Thickness(0, 0, 0, 12)
            group_box.Padding = Thickness(8)
            group_box.Background = SolidColorBrush(Colors.White)

            # WrapPanel с центрированием — КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ
            wrap = WrapPanel()
            wrap.HorizontalAlignment = HorizontalAlignment.Center  # Центрируем содержимое!
            wrap.VerticalAlignment = VerticalAlignment.Top
            wrap.Margin = Thickness(0)
            wrap.Background = SolidColorBrush(Colors.White)

            for room in grouped[group_name]:
                wrap.Children.Add(self._create_room_button(room))

            group_box.Content = wrap
            root_panel.Children.Add(group_box)

        scroll = ScrollViewer()
        scroll.VerticalScrollBarVisibility = ScrollBarVisibility.Auto
        scroll.Background = SolidColorBrush(Colors.White)
        scroll.Content = root_panel

        tab.Content = scroll
        return tab

    def _create_room_button(self, room):
        btn = Button()
        btn.Width = 87
        btn.Height = 50
        btn.Margin = Thickness(2)
        btn.Padding = Thickness(3, 2, 3, 0) 
        
        text = TextBlock()
        text.Text = room.Name or u"(без имени)"
        text.TextWrapping = TextWrapping.Wrap
        text.TextAlignment = TextAlignment.Center

        text.HorizontalAlignment = HorizontalAlignment.Center
        text.VerticalAlignment = VerticalAlignment.Top 
        
        text.LineHeight = 12
        text.LineStackingStrategy = 0


        btn.Content = text

        def on_click(sender, args):
            self.room_name = room.Name
            self.create_room_event.Raise()

            # forms.alert(
            #     u"Вы выбрали помещение:\n{}\nГруппа: {}".format(
            #         room.Name, room.Group
            #     ),
            #     exitscript=False

            # with Transaction(doc, 'Create Room Point') as t:
            #     t.Start()
            #     room = doc.Create.NewRoom(level, point)
            #     room.Name = "Комната по точке"
            #     t.Commit()

        btn.Click += on_click
        return btn
