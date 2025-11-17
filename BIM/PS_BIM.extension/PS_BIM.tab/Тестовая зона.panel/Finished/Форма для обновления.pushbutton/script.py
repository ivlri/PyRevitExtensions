# -*- coding: utf-8 -*-
from functions._Panel import PaswordPanel
import clr
from pyrevit import revit, EXEC_PARAMS
doc = revit.doc
passw = PaswordPanel(current_doc=doc)
c = passw.check_passward()
print(c)

# from pyrevit import forms
# import clr
# clr.AddReference("System.Windows.Forms")
# from System.Windows.Forms import TextBox, Form, DialogResult

# def ask_password():
#     form = Form()
#     form.Text = "Пароль"
#     textbox = TextBox()
#     textbox.UseSystemPasswordChar = True  # Включить маскировку
#     form.Controls.Add(textbox)
    
#     if form.ShowDialog() == DialogResult.OK:
#         return textbox.Text
#     return None

# password = ask_password()
# if password:
#     print("Пароль принят!")