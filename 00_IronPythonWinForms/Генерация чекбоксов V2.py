#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import clr
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")


from System.Drawing import *
from System.Windows.Forms import *
import System.IO

#------ Глобальные настройки формы ------#
bitmapImage = System.Drawing.Bitmap(
    r"Z:\01_Библиотека\02_Семейства\ALL_Основные надписи\Логотип\\" + "Логотип Партнер.png")  # Логотип
titleIcon = Icon.FromHandle(bitmapImage.GetHicon())
titleText = "Высота помещений"  # текст, который появляется в строке заголовка GUI
txtWith = 160 # ширина текстовой зоны
st_height = 30 # высота с кототорой начинается ввод
btnHeight = 40  # Высота кнопки
btnWidth = 100  # Ширина кнопки
btnSpacing = 20  # Интервал между кнопками + оступ элементов от края
htSpacing = 50  # Интервал между вводам данных
fontMessage = Font("Times New Roman ", 14)
fontCK = Font("Times New Roman ", 12)  # настройка шрифта у Checkbox
winSize = Size(400, 600)  # размеры winform (ширина(min = 300), высота).



def button(txt, loc, clc):
    btn = Button()
    # btnCancel.Parent = self
    btn.Text = txt
    btn.Anchor = (AnchorStyles.Bottom | AnchorStyles.Right)
    btn.Location = loc
    btn.Click += clc
    btn.Height = btnHeight
    btn.Width = btnWidth
    btn.BackColor = Color.FromArgb(220, 220, 220)
    return btn


def logo(uiH):
    logo = PictureBox()
    bitmapImage = System.Drawing.Bitmap(
        r"Z:\01_Библиотека\02_Семейства\ALL_Основные надписи\Логотип\\" + "Лого Партнер горизонтальный полный прозрачный фон.png")
    logo.Image = bitmapImage
    ratio = float(logo.Height) / float(logo.Width)  # должно быть значение с плавающей точкой, так как int округляется до ближайшего целого числа
    logo.Size = Size(200, 80 * ratio)  # размер логотипа
    logo.Location = Point(btnSpacing, (uiH - logo.Height) - btnSpacing)
    logo.SizeMode = PictureBoxSizeMode.Zoom  # масштабирование изображения
    logo.Anchor = (
                AnchorStyles.Bottom | AnchorStyles.Left)  # Привязка для охранения положения при масштабировании окна
    return logo



out = []
class WinForm(Form):
    def add_Logotxt(self, uiW, value):
        label_class = Label()
        font = fontMessage
        label_class.Text = value
        label_class.Font = font
        label_class.Location = Point(btnSpacing, btnSpacing)
        label_class.Height = htSpacing
        label_class.Width = uiW / 2
        return label_class

    def add_CHECKBOX(self, uiW, position=1,name="Пример ввода", value="Пример ввода!!"):
        ch_box = CheckBox()
        ch_box.Name = name
        ch_box.Text = value
        ch_box.Location = Point(btnSpacing, st_height + (position * htSpacing))
        ch_box.Width = uiW - (btnSpacing * 2)
        ch_box.Font = fontCK
        ch_box.Height = 40
        return ch_box

    def add_txtbox(self,uiW, position=1):#(self,uiW, count=1, value="Пример ввода") - если нужно в рамку добавить тест описания
        # окно ввода данных
        text_box = TextBox()
        text_box.Width = uiW / 2 - 2*btnSpacing
        #text_box.Text = value
        text_box.Font = fontCK
        text_box.Location = Point(htSpacing + txtWith, (st_height + htSpacing * position))
        return text_box

    def add_txtbox_label(self, position =1, name = "Пример ввода"):
        # текст возле ввода данных
        text_box_label = Label()
        text_box_label.Text = name
        text_box_label.Width = txtWith
        text_box_label.Font = fontCK
        text_box_label.Location = Point(btnSpacing, (st_height + htSpacing * position))
        text_box_label.Height = 50
        return text_box_label

    def add_combov_verd(self,uiW,position =1,name = "имя", value = ["Пример 1", 'Пример 2']):
        combov_verd = ComboBox()
        combov_verd.Name = name
        combov_verd.Font = fontCK
        combov_verd.Width = uiW / 2 - 2*btnSpacing
        combov_verd.Items.AddRange(System.Array[System.Object](value))
        combov_verd.Location = Point(htSpacing + txtWith, (st_height + htSpacing * position))
        return combov_verd


    def okButton_pressed(self, sender, args):
        numErrorProvider = System.Windows.Forms.ErrorProvider()
        try:

            for i in range(len(self.chBox_checks)):
                out.insert((self.lst_checkbox_index)[i], self.chBox_checks[i].Checked)

            self.Close()  # Тригер для закрытия окна
        except ValueError:
            numErrorProvider.SetError(sender, 'Ошибка')

    def __init__(self):
        #------ Настройка окна ------#
        self.CenterToScreen()  # открывать по центру экрана
        self.BringToFront()  # Выводить на предний план
        self.Icon = titleIcon
        self.Size = winSize
        uiWidth = self.DisplayRectangle.Width  # ширина формы для использования в классе
        uiHeight = self.DisplayRectangle.Height # высота формы для использования в классе
        self.Topmost = True # Отобрадение окна поверх других окон
        self.BackColor = Color.FromArgb(242, 242, 242)

        self.Controls.Add(logo(uiHeight))

        self.Text = titleText # Текст заголовка

        # Настройка текста в форме(можно добавить к кажой кнопке, но это гемор)

        self.Controls.Add(self.add_Logotxt(uiWidth,
                                      "Заполните значения")
                          )

        #----- добавить флажек() -----#
        self.start_position = 1
        self.chBox_checks = []
        self.lst_checkbox_index = []

        self.checkedListBox = CheckedListBox()



        # ----- добавить кнопку -----#
        btnOkClick = self.okButton_pressed  # Регистрация нажатия
        # Ниже одна кнопка. Для расчета нужно btnWidth * кол-во кнопок
        btnOkLoc = Point(uiWidth - ((btnWidth) + btnSpacing), uiHeight - (btnHeight + btnSpacing)) #Расчет положения.
        btnOk = button('OK', btnOkLoc, btnOkClick)
        self.Controls.Add(btnOk)


form = WinForm()
Application.Run(form)

print(out)
