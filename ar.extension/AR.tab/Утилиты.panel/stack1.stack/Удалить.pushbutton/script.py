# -*- coding: utf-8 -*-
__title__   = "Удалить помещения"
__doc__ = """
Описание: Позволяет удалять помещения без спек
"""

#==================================================
#IMPORTS
#==================================================

import os
import clr
import sys
import traceback

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

from pyrevit import forms
from rpw.ui.forms import (FlexForm, Label, TextBox,
                          Separator, Button, CheckBox, ComboBox)

from config import configs, apartutils
from functions.customselection import CustomSelections
from collections import defaultdict


#==================================================
#MAIN
#==================================================
doc, uidoc, app = configs.get_context()
doc_title = doc.Title
rooms = CustomSelections.pick_elements_by_category(built_in_category=BuiltInCategory.OST_Rooms, 
                                                        status="Выберете помещения для удаления"
                                                        )
with Transaction(doc, "Rooms_Удаление помещений") as t:
    t.Start()
    try:
        for room in rooms:
            doc.Delete(room.Id)
    except Exception:
        print(traceback.format_exc())
    finally:
        t.Commit()
