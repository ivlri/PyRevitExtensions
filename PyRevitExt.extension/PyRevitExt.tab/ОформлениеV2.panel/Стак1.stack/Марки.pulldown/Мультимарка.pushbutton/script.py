# -*- coding: utf-8 -*-
__title__   = "Мультимарка"
__doc__ = """
Модуль для добавления выносок к маркам

Этот скрипт позволяет добавлять дополнительные выноски к существующим маркам
или создавать новые марки.

Основные возможности:
- Позиционирование выносок относительно курсора
- Поддержка различных версий Revit (включая 2022 и выше)
- Возможность работать как на открытом виде так и на виде на листе

Версия: 1.0
Автор: David Medvedev 
"""
# ==================================================
# IMPORTS
# ==================================================

import clr
import System
import re
import sys
from clr import StrongBox
from math import fabs
import traceback

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Collections")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

import System.Windows.Forms
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from pyrevit import forms

from functions._CustomSelections import CustomSelections
from functions.version import rvt_vers

# Добавляем логирование использования инструмента
import os
from functions._logger import ToolLogger

ToolLogger(script_path=__file__).log()

# ==================================================
# GLOBALS
# ==================================================

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
active_view = doc.ActiveView
is_2022 = rvt_vers()

# ==================================================
# FUNCTIONS
# ==================================================


def concat_XYZ(xyz):
    """Конвертирует XYZ в строку"""
    x = str(xyz.X)
    y = str(xyz.Y)
    z = str(xyz.Z)
    return x + y + z


def get_active_ui_view(uidoc, mark=None):
    """
    Получает активный UI-вид Revit и, при необходимости, центрирует его по заданной марке.

    Параметры
    ---------
    uidoc : Autodesk.Revit.UI.UIDocument
        Активный UI-документ Revit.
    mark : Autodesk.Revit.DB.IndependentTag
        Марка, относительно которой выполняется центрирование.

    Возвращает
    ----------
    uiview : Autodesk.Revit.UI.UIView
        Активный UI-вид, соответствующий текущему документу.
    to_close : bool
        Флаг, указывающий, был ли открыт временный вид и требуется ли закрытие.
    port_owner_view : Autodesk.Revit.DB.View
        Вид-владелец viewport, если он найден.

    Описание
    --------
    Функция определяет UIView, связанный с текущим активным видом Revit.
    Если вид открыт в режиме редактирования через viewport(имеет недоступный
    bounding box) - временно открывает вид основу viewport. Иначе GetZoomCorners() даст некоренное значение.
    """

    doc = uidoc.Document
    view = doc.ActiveView
    uiview = None
    port = None
    port_owner_view = None
    to_close = False

    for i in FilteredElementCollector(doc).OfClass(Viewport).ToElements():
        if i.ViewId == view.Id:
            port = i
            port_owner_view = i.OwnerViewId
            break

    if port and port.get_BoundingBox(view) is None: # Если BoundingBox - None, то значит вид активирован 
        # Переключаемся на временный вид чтобы "разблокировать" текущий
        temp_view = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()[0]
        uidoc.ActiveView = temp_view
        v1 = uidoc.ActiveView.Id

        # Возвращаемся к нужному виду
        uidoc.ActiveView = view 
        v2 = uidoc.ActiveView.Id
        
        # Получаем все открытые UIViews
        uiviews = uidoc.GetOpenUIViews()
        to_close = True
        
        # Закрыть временный вид
        for uv in uiviews:
            if uv.ViewId.Equals(v1):
                uv.Close()
                break
        
        # Обновленный список UIViews
        uiviews = uidoc.GetOpenUIViews()
        
        for uv in uiviews:
            if uv.ViewId.Equals(v2):
                uiview = uv
                center_view_on_mark(doc, uiview, mark)
                break
                
        # Если не нашли, берем последний - только для одного случая
        if not uiview and uiviews:
            uiview = list(uiviews)[-1]
            center_view_on_mark(doc, uiview, mark)

    else:
        uiviews = uidoc.GetOpenUIViews()
        for uv in uiviews:
            if uv.ViewId.Equals(view.Id):
                uiview = uv
                break
            
    return uiview, to_close, doc.GetElement(port_owner_view)

def center_view_on_mark(doc, uiview, mark):
    """
    Центрирует UI-вид на заданной марке.

    Параметры
    ---------
    doc : Autodesk.Revit.DB.Document
        Текущий документ Revit.
    uiview : Autodesk.Revit.UI.UIView
        UI-представление активного вида.
    mark : Autodesk.Revit.DB.IndependentTag
        Марка, по которой выполняется центрирование.

    Описание
    --------
    Функция получает bounding box марки относительно текущего вида,
    вычисляет ограничивающий прямоугольник и выполняет масштабирование-центрирование
    через `ZoomAndCenterRectangle`. Дополнительно выполняется небольшой зум для
    сохранения удобства навигации.
    """

    try:
        System.Windows.Forms.Application.DoEvents() #  Просто для обновления UI интерфейса. Иначе не успеет обработать BBox
        mark_bbox = mark.get_BoundingBox(doc.GetElement(uiview.ViewId))
        pt1 = XYZ(mark_bbox.Min.X, mark_bbox.Min.Y, mark_bbox.Min.Z)
        pt2 = XYZ(mark_bbox.Max.X, mark_bbox.Max.Y, mark_bbox.Max.Z)

        uiview.ZoomAndCenterRectangle(pt2, pt1)
        uiview.Zoom(0.6)
        
    except Exception as ex:
        print(traceback.format_exc())

        
def get_coordinate(uiview):
    """
    Определяет координаты курсора в пространстве 3D Revit вида.

    Параметры
    ---------
    uiview : Autodesk.Revit.UI.UIView
        UI-представление вида, из которого получаются координаты.

    Возвращает
    ----------
    Autodesk.Revit.DB.XYZ
        Точка в координатах модели, соответствующая положению курсора.

    Описание
    --------
    Использует координаты окна вида и текущую позицию курсора Windows, чтобы
    вычислить нормализованные экранные координаты. Далее они проецируются
    в модельное пространство на основе направления RightDirection и UpDirection
    текущего вида.
    """

    rect = uiview.GetWindowRectangle()
    p = System.Windows.Forms.Cursor.Position
    
    dx = float(p.X - rect.Left) / float(rect.Right - rect.Left)
    dy = float(p.Y - rect.Bottom) / float(rect.Top - rect.Bottom)
    
    v_right = active_view.RightDirection
    v_right = XYZ(fabs(v_right.X), fabs(v_right.Y), fabs(v_right.Z))
    v_up = active_view.UpDirection
    v_up = XYZ(fabs(v_up.X), fabs(v_up.Y), fabs(v_up.Z))
    
    dxyz = dx * v_right + dy * v_up
    corners = uiview.GetZoomCorners()
    a = corners[0]
    b = corners[1]
    v = b - a
    q = a + dxyz.X * v.X * XYZ.BasisX + dxyz.Y * v.Y * XYZ.BasisY + dxyz.Z * XYZ.BasisZ * v.Z
    return q


def get_tagged_element(mark):
    """
    Возвращает элемент, на который ссылается марка.

    Параметры
    ---------
    mark : Autodesk.Revit.DB.IndependentTag
        Марка, из которой извлекается связанный элемент.

    Возвращает
    ----------
    Autodesk.Revit.DB.Element
        Элемент, к которому привязана марка.

    Описание
    --------
    Обрабатывает различия API Revit между версиями 2022 и 2023+,
    Для новых версий используется свойство `TaggedLocalElementId`,
    для старых — массив ссылок `GetTaggedLocalElements()`.
    """

    if is_2022:
        return doc.GetElement(mark.TaggedLocalElementId)
    else:
        return mark.GetTaggedLocalElements()[0]


def create_new_mark(mark, tagget, pos, elbow_loc):
    """
    Создаёт новую марку для элемента и задаёт ей корректную выноску.

    Параметры
    ---------
    mark : Autodesk.Revit.DB.IndependentTag
        Исходная марка, чьи настройки используются.
    tagget : Autodesk.Revit.DB.Element
        Элемент, который должен быть отмечен новой маркой.
    pos : Autodesk.Revit.DB.XYZ
        Конечная точка выноски.
    new_middle : Autodesk.Revit.DB.XYZ
        Точка локтя выноски.
    head : Autodesk.Revit.DB.XYZ
        Позиция головы марки.

    Описание
    --------
    Создаёт новую марку того же типа и ориентации, настраивает геометрию выноски.
    При несоответствии текста автоматически удаляет марку, предотвращая ошибки
    дублирования и некорректных типов марок.
    """

    ref = Reference(tagget)
    
    with Transaction(doc, 'Добавить выноску марки') as t:
        t.Start()
        
        new_mark = IndependentTag.Create(
            doc, 
            mark.GetTypeId(), 
            doc.ActiveView.Id, 
            ref, 
            True, 
            mark.TagOrientation, 
            pos
        )
        
        new_mark.TagHeadPosition = mark.TagHeadPosition
        new_mark.LeaderEndCondition = mark.LeaderEndCondition

        if is_2022:
            new_mark.LeaderEnd = pos

            if elbow_loc:
                new_mark.LeaderElbow = elbow_loc

            if new_mark.TagText != mark.TagText:
                doc.Delete(new_mark.Id)
        else:
            new_mark.SetLeaderElbow(ref, elbow_loc)
            new_mark.SetLeaderEnd(ref, pos)
        t.Commit()


def add_reference_to_existing_mark(mark, tagget, pos, elbow_loc):
    """
    Добавляет новую ссылку в существующую марку и обновляет её выноску.

    Параметры
    ---------
    mark : Autodesk.Revit.DB.IndependentTag
        Марка, в которую добавляется дополнительный элемент.
    tagget : Autodesk.Revit.DB.Element
        Элемент, к которому создаётся новая выноска.
    pos : Autodesk.Revit.DB.XYZ
        Конечная точка новой выноски.
    new_middle : Autodesk.Revit.DB.XYZ
        Точка локтя новой выноски.

    Описание
    --------
    Добавляет новый reference к существующей марке без создания новой(Revit 2023+)
    """

    ref = Reference(tagget)
    refList = List[Reference]()
    refList.Add(ref)
    
    with Transaction(doc, 'Добавить выноску марки') as t:
        t.Start()

        mark.AddReferences(refList)
        mark.SetLeaderElbow(ref, elbow_loc)
        mark.SetLeaderEnd(ref, pos)
            
        t.Commit()


def get_leader_elbow(mark):
    try:
        return mark.LeaderElbow
    except:
        tagged_refs = mark.GetTaggedReferences()
        return mark.GetLeaderElbow(tagged_refs[0])


# ==================================================
# MAIN
# ==================================================
try:
    with forms.WarningBar(title='Выберите марку:'):
        mark = CustomSelections.pick_element_by_class(IndependentTag)
        uiview, to_close, port_owner_view = get_active_ui_view(uidoc, mark)

    if not mark:
        sys.exit()

    # Получение начальных данных
    el = get_tagged_element(mark)
    el_category = el.Category

    elbow_loc = get_leader_elbow(mark)
    head = mark.TagHeadPosition
    tagget = True


    with forms.WarningBar(title='Выберите следующий элемент для привязки (Следите за положением курсора!!!):'):
        while tagget:
            tagget = CustomSelections.pick_element_by_category(el_category)

            if tagget:
                pos = get_coordinate(uiview)
                
                if tagget.Id == el.Id:
                    create_new_mark(mark, tagget, pos, elbow_loc)
                else:
                    add_reference_to_existing_mark(mark, tagget, pos, elbow_loc)
except:
    print(traceback.format_exc())
finally:
    if to_close:
        uiview.Close()
        uidoc.ActiveView = port_owner_view