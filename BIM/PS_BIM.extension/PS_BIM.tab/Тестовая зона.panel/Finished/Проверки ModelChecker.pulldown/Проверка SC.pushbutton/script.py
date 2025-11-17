# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================
from functions import mcrun
from pyrevit import forms
import Autodesk.Windows as aw
import time 

with forms.ProgressBar(indeterminate=True, cancellable=True) as pb:
    doc   = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument
    uiapp = uidoc.Application
    app   = __revit__.Application
        
    pb._title = 'Проверка'
    max_value = 10
    for counter in range(0, max_value):
        if pb.cancelled:
            break
        else:
            pb.update_progress(counter, max_value)

    mcrun.MCRunner(doc, uiapp, 'SC').run()
