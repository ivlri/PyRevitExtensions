# -*- coding: utf-8 -*- 
#pylint: disable=import-error,invalid-name,broad-except,superfluous-parens
#pylint: disable=unused-import,wrong-import-position,unused-argument
#pylint: disable=missing-docstring
import sys
import time
import os.path as op

from pyrevit import HOST_APP, framework
from pyrevit import revit, DB, UI
from pyrevit import forms
from pyrevit import routes


forms.open_dockable_panel("3110e336-f81c-4927-87da-4e0d30d4d64a")
