# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================
from functions import mcrun
from pyrevit import forms
import Autodesk.Windows as aw
import time 
import os
from functions._logger import ToolLogger
ToolLogger(script_path=__file__).log()
with forms.ProgressBar(indeterminate=True, cancellable=True) as pb:
    doc   = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument
    uiapp = uidoc.Application
    app   = __revit__.Application
    
    pb._title = 'Проверка'
    max_value = 10
    for counter in range(0, max_value-1):
        if pb.cancelled:
            break
        else:
            pb.update_progress(counter, max_value-1)

    mcrun.MCRunner(doc, uiapp, 'AR_Rooms').run()