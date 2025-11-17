# -*- coding: utf-8 -*-
__title__   = "Поворот\nаннотаций"
__doc__ = """Описание:

Используется для оформления типовых секций с поворотом в одном файле. 
После оформления исходного вида -> этот вид копируется и поворачивается на нужный угол -> после запуска, 
скрипт определит этот угол и проведет поворот всех аннотаций, для которых это технически возможно.
"""
#==================================================
#IMPORTS
#==================================================

import os
import codecs
import time
import math

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.Exceptions import InvalidOperationException

# .NET Imports
import clr
clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Collections")
import System
from System.Collections.Generic import List
import System.Windows.Forms

from pyrevit import forms
from pyrevit import revit, DB, UI