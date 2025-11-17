# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Collections")

import System
clr.AddReference("RevitAPI")
import Autodesk

clr.AddReference("RevitAPIUI")

import re
import sys
import System.Windows.Forms
from clr import StrongBox
from System.Collections.Generic import IList
from math import fabs

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import Rebar
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter, ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from functions._CustomSelections import CustomSelections

#==================================================
#VARIABLES
#==================================================

#==================================================
#MAIN
#==================================================
def start():
    uidoc = __revit__.ActiveUIDocument
    doc = uidoc.Document
    active_view = doc.ActiveView
    
    mark = CustomSelections.pick_element_by_class(IndependentTag, status="1) Выберете марку по который произвести выравнивание")
    if mark:
        el = doc.GetElement(mark.TaggedElementId.HostElementId).Category

        try:
            middle = mark.LeaderElbow
        except:
            middle = False

        head = mark.TagHeadPosition
        point = mark.LeaderEnd

        taggets = CustomSelections.pick_elements_by_class(IndependentTag, status="2) Выберете марки которые нужно перенести")

        with Transaction(doc, "Выровнять марки") as t:
            t.Start()
            for tag in taggets:
                tag.TagHeadPosition = head

                if middle:
                    tag.LeaderElbow = middle
            t.Commit()
