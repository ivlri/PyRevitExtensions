# -*- coding: utf-8 -*-
#⬇️ Imports
import clr
from pyrevit import revit, EXEC_PARAMS
from functions._Panel import PaswordPanel

#📦 Variables
sender = __eventsender__  # UIApplication
args = __eventargs__      # Autodesk.Revit.UI.Events.BeforeExecutedEventArgs

doc = revit.doc

# Список разрешенных пользователей, для которых не нужно вводить пароль
allowed_users = []

# Если текущий пользователь не в списке разрешенных, показываем окно с паролем
passw = PaswordPanel(current_doc=doc, 
          current_sender=sender, 
          current_args=args,
          info=False,
          allowed_users=allowed_users)

passw.check_passward()
