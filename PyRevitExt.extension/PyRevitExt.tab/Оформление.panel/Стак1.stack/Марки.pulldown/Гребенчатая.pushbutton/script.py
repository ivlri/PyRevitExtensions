# -*- coding: utf-8 -*-
__title__   = "Гребенчатая"
__doc__ = """
Модуль для добавления выносок к маркам

Этот скрипт позволяет добавлять дополнительные выноски к существующим маркам
или создавать новые марки для элементов с аналогичным стилем оформления.

Основные возможности:
- Копирование стиля существующей марки для новых выносок
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
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.Exceptions import OperationCanceledException, ArgumentOutOfRangeException
from pyrevit import forms

from functions._CustomSelections import CustomSelections
from functions._sketch_plane import set_sketch_plane_to_viewsection
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
IS_2022 = rvt_vers()

# ==================================================
# FUNCTIONS
# ==================================================


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
        temp_view = doc.GetElement(ElementId(4641555))  # Ваш временный вид
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

    if IS_2022:
        return doc.GetElement(mark.TaggedLocalElementId)
    else:
        return mark.GetTaggedLocalElements()[0]


def get_leader_points(mark):
    """
    Получает ключевые точки выноски марки: локоть, позицию головы и конечную точку.

    Параметры
    ---------
    mark : Autodesk.Revit.DB.IndependentTag
        Марка с выноской.

    Возвращает
    ----------
    (middle, head, point) : tuple(Autodesk.Revit.DB.XYZ)
        Координаты локтя, головы и конца выноски.

    Описание
    --------
    Обрабатывает различия API Revit между версиями 2022 и 2023+,
    """

    if IS_2022:
        # Для Revit 2022 используем свойства
        middle = mark.LeaderElbow
        point = mark.LeaderEnd
    else:
        tagged_ref = mark.GetTaggedReferences()[0]

        middle = mark.GetLeaderElbow(tagged_ref)
        point = mark.GetLeaderEnd(tagged_ref)
    
    head = mark.TagHeadPosition
    return middle, head, point


def signed_distance_to(plane, p):
    """Вычисляет signed distance до плоскости"""
    v = p - plane.Origin
    return plane.Normal.DotProduct(v)


def project_onto(plane, p):
    """Проецирует точку на плоскость"""
    d = signed_distance_to(plane, p)
    return p - d * plane.Normal


def calculate_leader_geometry(mark, pos, plane):
    """
    Вычисляет новую геометрию выноски на основе исходной марки и положения курсора.

    Параметры
    ---------
    mark : Autodesk.Revit.DB.IndependentTag
        Базовая марка.
    pos : Autodesk.Revit.DB.XYZ
        Позиция курсора в координатах модели.
    plane : Autodesk.Revit.DB.Plane
        Плоскость текущего вида.

    Возвращает
    ----------
    new_middle : Autodesk.Revit.DB.XYZ
        Новая точка локтя выноски.
    head_proj : Autodesk.Revit.DB.XYZ
        Проецированная точка головы марки.

    Описание
    --------
    Проецирует все ключевые точки марки на плоскость вида,
    вычисляет пересечение направляющих линий для определения нового локтя,
    обеспечивая направление выноски относительно исходной геометрии.
    """

    middle, head, point = get_leader_points(mark)

    # Проецирование точки на плоскость вида
    middle_proj = project_onto(plane, middle)
    head_proj = project_onto(plane, head)
    point_proj = project_onto(plane, point)
    pos_proj = project_onto(plane, pos)

    # Вычисление пересечения линий для нового локтя 
    vec = (point_proj - middle_proj).Normalize()
    line1 = Line.CreateUnbound(pos_proj, vec)
    line2 = Line.CreateUnbound(middle_proj, (head_proj - middle_proj).Normalize())
    
    intersection = StrongBox[IntersectionResultArray]()
    line1.Intersect(line2, intersection)
    
    new_middle = list(intersection.Value)[0].XYZPoint
    return new_middle, head_proj


def create_new_mark(mark, tagget, pos, new_middle, head):
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
    
    with Transaction(doc, 'Добавить выноску') as t:
        t.Start()
        
        new_mark = IndependentTag.Create(
            doc, 
            mark.GetTypeId(), 
            doc.ActiveView.Id, 
            ref, 
            True, 
            mark.TagOrientation, 
            head
        )
        
        new_mark.TagHeadPosition = head
        new_mark.LeaderEndCondition = mark.LeaderEndCondition
        
        if IS_2022:
            new_mark.LeaderElbow = new_middle
            new_mark.LeaderEnd = pos
        else:
            new_mark.SetLeaderElbow(ref, new_middle)
            new_mark.SetLeaderEnd(ref, pos)
        
        if new_mark.TagText != mark.TagText:
            doc.Delete(new_mark.Id)
            
        t.Commit()


def add_reference_to_existing_mark(mark, tagget, pos, new_middle):
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
        mark.SetLeaderElbow(ref, new_middle)
        mark.SetLeaderEnd(ref, pos)
            
        t.Commit()


# ==================================================
# MAIN
# ==================================================
with Transaction(doc, 'Добавить выноску марки') as t:
    t.Start()
try:

    with forms.WarningBar(title='Выберите текстовую аннотацию:'):
        mark = CustomSelections.pick_element_by_class(IndependentTag)
        uiview, to_close, port_owner_view = get_active_ui_view(uidoc, mark)

    if not mark:
        sys.exit()

    # ---- Получение начальных данных ----
    el = get_tagged_element(mark)
    el_category = el.Category

    plane = Plane.CreateByNormalAndOrigin(active_view.ViewDirection, active_view.Origin)
    tagget = True

    with forms.WarningBar(title='Выберите следующий элемент для привязки (Следите за положением курсора!!!):'):
        while tagget:
            tagget = CustomSelections.pick_element_by_category(el_category)
            
            if tagget:
                pos = get_coordinate(uiview)
                new_middle, head = calculate_leader_geometry(mark, pos, plane)
                
                if tagget.Id == el.Id:
                    create_new_mark(mark, tagget, pos, new_middle, head)
                else:
                    add_reference_to_existing_mark(mark, tagget, pos, new_middle)

except ArgumentOutOfRangeException:
    forms.alert('Не корректно установлен локоть. Установите точку локтя вдоль линии полки как показано на картинке!')
    print(traceback.format_exc())
except System.ArgumentOutOfRangeException:
    forms.alert('У марки отсутствуют выноски. Установите правильно начальную выноску и попробуйте еще раз.')
    print(traceback.format_exc())
except Exception as ex:
    print(traceback.format_exc())
finally:
    if to_close:
        uiview.Close()
        uidoc.ActiveView = port_owner_view