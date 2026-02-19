# # -*- coding: utf-8 -*-
__title__ = 'Панель'
__doc__ = 'Описание: Открывает панель создания помещений'

from pyrevit import forms
from panels.rpanel import RoomsDockablePanel

# # регистрация панели
forms.register_dockable_panel(RoomsDockablePanel)

# показать / активировать
# forms.open_dockable_panel(RoomsDockablePanel.panel_id)

