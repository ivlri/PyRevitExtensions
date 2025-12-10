# -*- coding: utf-8 -*-
__title__   = "Обновление подписей"
__doc__ = """Описание: Функция обновления подписей в проекте. Если человек больше у нас не работает и его подпись не используется на листе, то семейство подписи будет удалено."""

#==================================================
#IMPORTS
#==================================================
import os
import clr
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
import sys
import re
from System.Collections.Generic import List
clr.AddReference('System.IO')
from pyrevit import forms
import json
import codecs

# Добавляем логирование использования инструмента
# import os
# from functions._logger import ToolLogger
# ToolLogger(script_path=__file__).log() 

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
uiapp   = __revit__
act_view = doc.ActiveView

def shorten_fio(full_names):
    out = []
    for full_name in full_names:
        parts = full_name.split()
        if len(parts) < 3:
            return full_name 
        last_name = parts[0]
        initials = parts[1][0]# + parts[2][0]
        out.append(last_name + initials)
        out.append(last_name + initials + parts[2][0])
    return out

from pyrevit import script
from pyrevit.coreutils.logger import get_logger
from pyrevit import HOST_APP, EXEC_PARAMS, DOCS, BIN_DIR
from pyrevit import revit, UI, DB
from pyrevit import forms
from pyrevit import coreutils
from pyrevit import versionmgr
mlogger = get_logger(__name__)
def alert(msg, title='Обновление семейств', sub_msg=None, expanded=None, footer='',
          ok=True, cancel=False, yes=False, no=False, retry=False,
          warn_icon=True, options=None, exitscript=False):
    """Show a task dialog with given message.

    Args:
        msg (str): message to be displayed
        title (str, optional): task dialog title
        sub_msg (str, optional): sub message
        expanded (str, optional): expanded area message
        ok (bool, optional): show OK button, defaults to True
        cancel (bool, optional): show Cancel button, defaults to False
        yes (bool, optional): show Yes button, defaults to False
        no (bool, optional): show NO button, defaults to False
        retry (bool, optional): show Retry button, defaults to False
        options(list[str], optional): list of command link titles in order
        exitscript (bool, optional): exit if cancel or no, defaults to False

    Returns:
        bool: True if okay, yes, or retry, otherwise False

    Example:
        >>> from pyrevit import forms
        >>> forms.alert('Are you sure?',
        ...              ok=False, yes=True, no=True, exitscript=True)
    """
    # BUILD DIALOG
    cmd_name = EXEC_PARAMS.command_name
    if not title:
        title = cmd_name if cmd_name else 'pyRevit'
    tdlg = UI.TaskDialog(title)

    # process input types
    just_ok = ok and not any([cancel, yes, no, retry])

    options = options or []
    # add command links if any
    if options:
        clinks = coreutils.get_enum_values(UI.TaskDialogCommandLinkId)
        max_clinks = len(clinks)
        for idx, cmd in enumerate(options):
            if idx < max_clinks:
                tdlg.AddCommandLink(clinks[idx], cmd)
    # otherwise add buttons
    else:
        buttons = coreutils.get_enum_none(UI.TaskDialogCommonButtons)
        if yes:
            buttons |= UI.TaskDialogCommonButtons.Yes
        elif ok:
            buttons |= UI.TaskDialogCommonButtons.Ok

        if cancel:
            buttons |= UI.TaskDialogCommonButtons.Cancel
        if no:
            buttons |= UI.TaskDialogCommonButtons.No
        if retry:
            buttons |= UI.TaskDialogCommonButtons.Retry
        tdlg.CommonButtons = buttons

    # set texts
    tdlg.MainInstruction = msg
    tdlg.MainContent = sub_msg
    tdlg.ExpandedContent = expanded
    if footer:
        footer = footer.strip() + '\n'
    tdlg.FooterText = footer + 'pyRevit {}'.format(
        versionmgr.get_pyrevit_version().get_formatted()
        )
    tdlg.TitleAutoPrefix = False

    # set icon
    icons = {
        None: UI.TaskDialogIcon.TaskDialogIconNone,
        'error': UI.TaskDialogIcon.TaskDialogIconError,
        'warn': UI.TaskDialogIcon.TaskDialogIconWarning,
        'info': UI.TaskDialogIcon.TaskDialogIconInformation,
    }
    tdlg.MainIcon = icons[warn_icon]
       
    # tdlg.VerificationText = 'verif'

    # SHOW DIALOG
    res = tdlg.Show()

    # PROCESS REPONSES
    # positive response
    mlogger.debug('alert result: %s', res)
    if res == UI.TaskDialogResult.Ok \
            or res == UI.TaskDialogResult.Yes \
            or res == UI.TaskDialogResult.Retry:
        if just_ok and exitscript:
            sys.exit()
        return True
    # negative response
    elif res == coreutils.get_enum_none(UI.TaskDialogResult) \
            or res == UI.TaskDialogResult.Cancel \
            or res == UI.TaskDialogResult.No:
        if exitscript:
            sys.exit()
        else:
            return False

    # command link response
    elif 'CommandLink' in str(res):
        tdresults = sorted(
            [x for x in coreutils.get_enum_values(UI.TaskDialogResult)
             if 'CommandLink' in str(x)]
            )
        residx = tdresults.index(res)
        return options[residx]
    elif exitscript:
        sys.exit()
    else:
        return False
    
forms.alert = alert
#==================================================
#MAIN
#==================================================
#---Получение семейств
famly_symbols = FilteredElementCollector(doc).OfClass(Family).ToElements()
signs = filter(lambda x: "PS_Подпись" in x.Name, famly_symbols)

if signs:
    #--- Подготовка
    SIGNS_PATCH = r'\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\01_Рабочие задачи\ALL_Основные надписи\Подписи'
    PS_USERS_FILE = SIGNS_PATCH + r"\00_Список пользователей Revit.json"
    DOC_NAME = doc.Title
    USER_TO_PROD = {
        "AR": ["AR", "SC","ALL"],
        "SC": ["SC","ALL"],
        "AS": ["SC","ALL"],
        "HVAC": ["HVAC","ALL"],
        "WSS": ["WSS","ALL"]
    }

    with codecs.open(PS_USERS_FILE, 'r', encoding='utf-8') as f:
        PS_USERS = json.load(f)

    file_type = [prod for prod, users in USER_TO_PROD.items() if prod in DOC_NAME][0]

    #--- Все пользователи для файла
    users = ["Нет"]
    for us in USER_TO_PROD[file_type]:
        users.extend(shorten_fio(PS_USERS[us]))


    #---Получение используемых подписей(что бы не удалять)
    base_frame_symbols = filter(lambda x: x.Name == "PS_Основная надпись", famly_symbols)[0].GetFamilySymbolIds()
    use_signs = []
    for frame in base_frame_symbols:
        v01 = doc.GetElement(doc.GetElement(frame).LookupParameter("Подпись Строка 1 по комплекту").AsElementId()).Family.Name.split('_')[-1]
        v02 = doc.GetElement(doc.GetElement(frame).LookupParameter("Подпись Строка 2 по комплекту").AsElementId()).Family.Name.split('_')[-1]
        v03 = doc.GetElement(doc.GetElement(frame).LookupParameter("Подпись Строка 3 по комплекту").AsElementId()).Family.Name.split('_')[-1]
        v04 = doc.GetElement(doc.GetElement(frame).LookupParameter("Подпись Строка 4 по комплекту").AsElementId()).Family.Name.split('_')[-1]
        v05 = doc.GetElement(doc.GetElement(frame).LookupParameter("Подпись Строка 5 по комплекту").AsElementId()).Family.Name.split('_')[-1]
        v06 = doc.GetElement(doc.GetElement(frame).LookupParameter("Подпись Строка 6 по комплекту").AsElementId()).Family.Name.split('_')[-1]
        use_signs.extend([v01,v02,v03,v04,v05,v06])
    use_signs = set(use_signs)

    #---Проверка/Удаление/Загрузка семейств
    signs_to_doc = []
    sign_files = {os.path.splitext(os.path.basename(os.path.join(SIGNS_PATCH, f)))[0].split('_')[-1]: os.path.join(SIGNS_PATCH, f) 
                for f in os.listdir(SIGNS_PATCH) if f.lower().endswith('.rfa')}

    deleted_sings = []
    not_deleted_sings = []
    with Transaction(doc, 'PS_Удаление старых подписей') as t:
        t.Start()
        for sign in signs:
            sign_username = sign.Name.split("_")[-1]
            if sign_username in use_signs and sign_username != 'Подпись' and sign_username not in users:
                not_deleted_sings.append(sign_username)
                continue
            if sign_username not in users and sign.Name != "PS_Подпись":# and sign_username not in use_signs:
                deleted_sings.append(sign_username)
                doc.Delete(sign.Id)
                continue
            signs_to_doc.append(sign_username)
        t.Commit()

    loaded_signs = []
    with Transaction(doc, 'PS_Загрузка подписей') as t:
        t.Start()
        for sign_name, sign_file in sign_files.items():
            if sign_name not in signs_to_doc and sign_name in users:
                fam = doc.LoadFamily(sign_file)
                loaded_signs.append(sign_name)
        t.Commit()

    forms.alert('-Было удалено подписей: {}\n    {}\n-Было загружено подписей: {}\n    {} \
                \n-Есть в штампе,но нет в компании: {}\n    {}'.format(
                                                                len(deleted_sings),
                                                                '\n    '.join(deleted_sings),
                                                                len(loaded_signs),
                                                                '\n    '.join(loaded_signs),
                                                                len(not_deleted_sings),
                                                                '\n    '.join(not_deleted_sings)),
                title='Обновление подписей', 
                warn_icon='info')


