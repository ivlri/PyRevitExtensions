# -*- coding: utf-8 -*- 
__title__ = 'Открыть виды'
__doc__ = """Эта кнопка открывает несколько выделенных видов одним нажатием, чтобы сэкономить время, которое тратится на рендеринг при открытии тяжелых видов(Например фасадов).
Контекст: Должны быть выбраны несколько видов в браузере проекта или на листе"""
__context__ = 'Selection'

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import revit
    selection = revit.get_selection()
    uidoc = revit.uidoc
else:
    from revitutils import selection, uidoc

from Autodesk.Revit.UI import TaskDialog

sel = selection.elements
sel_count = len(sel)

errors = 0
for v in sel:
    try:
        uidoc.ActiveView = v
    except:
        errors += 1

# Вывод сообщений при неправильном выборе 
if sel_count == 0:
    TaskDialog.Show(__title__, "Выбирите 2 и более видов для открытия")
elif errors == sel_count:
    TaskDialog.Show(__title__, "Не удаетсся открыть виды")
elif errors != 0:
    TaskDialog.Show(__title__, "%d из %d выбраных видов открыты" % (sel_count - errors, sel_count))