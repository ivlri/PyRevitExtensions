# -*- coding: utf-8 -*-
def rvt_vers():
    app   = __revit__.Application
    if int(app.VersionNumber) <= 2022:
        return True

    return False