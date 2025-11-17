import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('System')
from System.Collections.Generic import List

clr.AddReference('RevitNodes')
import Revit
from Revit.Elements import *

clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference('System.Drawing')
clr.AddReference('System.Windows.Forms')
import System.Drawing
import System.Windows.Forms

from System.Drawing import *
from System.Windows.Forms import *

clr.AddReference('System.Data')
from System.Data import *

# ----- Основные переменные -----#
doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

link = UnwrapElement(IN[0])
LinkDoc = link.GetLinkDocument()
LincActiveProjectLocation = LinkDoc.ActiveProjectLocation
LinkProjectLocations = LinkDoc.ProjectLocations

id_DocSiteLocation = doc.SiteLocation.Id

fontCK = Font("Times New Roman ", 12)
fontBT = Font("Times New Roman ", 10)
bitmapImage = System.Drawing.Bitmap(
    r"\\fs\public\Холдинг\ПоревитД\ТИМ\01_Библиотека\02_Семейства\ALL_Основные надписи\Логотип" + "\\Логотип Партнер.png")  # Логотип
titleIcon = Icon.FromHandle(bitmapImage.GetHicon())


# ----- Область функций -----#\
def get_DocProjectLocationsNames():
    lst = []
    for ProjectLocation in doc.ProjectLocations:
        lst.append(ProjectLocation.Name)
    return lst


def get_LinkProjectLocationsNames():
    lst = []
    for ProjectLocation in LinkDoc.ProjectLocations:
        lst.append(ProjectLocation.Name)
    return lst


def get_LinkProjectPosition():
    pos = []
    for ProjectLocation in LinkDoc.ProjectLocations:
        pos.append(ProjectLocation.GetProjectPosition(XYZ(0, 0, 0)))
    return pos


def Create_DocProjectLocation(result):
    res = []
    for j in result:
        res.append(j.Name)
    ProjectPosition = get_LinkProjectPosition()

    DocProjectLocationsNames = get_DocProjectLocationsNames()
    for i in res:
        if not i in DocProjectLocationsNames:
            ProjectLocation.Create(
                doc,
                id_DocSiteLocation,
                i
            )
        else:
            continue
    return True


def get_ListFromSet(lst):
    re = []
    for i in lst:
        re.append(i)
    return re


def tolist(obj1):
    if hasattr(obj1, "__iter__"):
        return obj1
    else:
        return [obj1]


def get_xyz(i):
    xyz = XYZ(i.X / 304.8, i.Y / 304.8, i.Z / 304.8)
    return xyz


# ----- Данне из связи связи -----#
ListLinkProjectLocations = get_ListFromSet(LinkProjectLocations)


# ----- Класс Winform -----#
class Form24(Form):
    def __init__(self, lstSchedule, lstValue):
        self._tableData = DataTable("Data")
        self._tableData.Columns.Add("Key", System.String)
        self._tableData.Columns.Add("Value", System.Object)
        # populate dataTable
        [self._tableData.Rows.Add(key_, value_) for key_, value_ in zip(lstSchedule, lstValue)]
        self.out = []
        self.InitializeComponent()

    def InitializeComponent(self):
        self._checkedListBox1 = System.Windows.Forms.CheckedListBox()
        self._checkBoxSelectAll = System.Windows.Forms.CheckBox()
        self._button1 = System.Windows.Forms.Button()
        self.SuspendLayout()
        self.CenterToScreen()
        self.Icon = titleIcon

        #
        # checkedListBox1
        #
        self._checkedListBox1.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right
        self._checkedListBox1.FormattingEnabled = True
        self._checkedListBox1.CheckOnClick = True
        self._checkedListBox1.Location = System.Drawing.Point(12, 30)
        self._checkedListBox1.Name = "checkedListBox1"
        self._checkedListBox1.DataSource = self._tableData
        self._checkedListBox1.DisplayMember = "Key"
        self._checkedListBox1.Size = System.Drawing.Size(300, 400)
        self._checkedListBox1.TabIndex = 0
        self._checkedListBox1.Font = fontCK
        #
        # checkBoxSelectAll
        #
        self._checkBoxSelectAll.Anchor = System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left
        self._checkBoxSelectAll.Location = System.Drawing.Point(12, 450)
        self._checkBoxSelectAll.Name = "checkBoxSelectAll"
        self._checkBoxSelectAll.Size = System.Drawing.Size(150, 24)
        self._checkBoxSelectAll.TabIndex = 1
        self._checkBoxSelectAll.Text = "Выбрать все"
        self._checkBoxSelectAll.UseVisualStyleBackColor = True
        self._checkBoxSelectAll.CheckedChanged += self.CheckBoxSelectAllCheckedChanged
        self._checkBoxSelectAll.Font = fontBT
        #
        # button1
        #
        self._button1.Anchor = System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right
        self._button1.Location = System.Drawing.Point(235, 450)
        self._button1.Name = "button1"
        self._button1.Size = System.Drawing.Size(75, 27)
        self._button1.TabIndex = 2
        self._button1.Text = "OK"
        self._button1.UseVisualStyleBackColor = True
        self._button1.Click += self.Button1Click
        self._button1.Font = fontBT
        #
        # Form24
        #
        self.ClientSize = System.Drawing.Size(325, 500)
        self.Controls.Add(self._button1)
        self.Controls.Add(self._checkBoxSelectAll)
        self.Controls.Add(self._checkedListBox1)
        self.Name = "It's magic ≽^•⩊•^≼"
        self.Text = "It's magic ≽^•⩊•^≼"
        self.ResumeLayout(False)

    def CheckBoxSelectAllCheckedChanged(self, sender, e):
        for i in range(self._checkedListBox1.Items.Count):
            self._checkedListBox1.SetItemChecked(i, sender.Checked)

    def Button1Click(self, sender, e):
        self.out = [row['Value'] for row in self._checkedListBox1.CheckedItems]
        self.Close()


toList = lambda x: x if hasattr(x, '__iter__') else [x]

# Активания формы
lstSchedules = [name for name in get_LinkProjectLocationsNames()]
ValueList = [i for i in range(len(lstSchedules))]
objForm = Form24(lstSchedules, ValueList)
objForm.ShowDialog()

out = objForm.out
Result = []
for i in out:
    Result.append(ListLinkProjectLocations[i])
# ----- Преобраования координационной системы -----#

link = UnwrapElement(IN[0])
linkDoc = link.GetLinkDocument()
transform = link.GetTotalTransform().ToCoordinateSystem(1)

Set_Point = get_xyz(transform.Origin)
# ----- Область скрипта -----#
TransactionManager.Instance.EnsureInTransaction(doc)
# 1.Сосздание площадок в проекте
test = Create_DocProjectLocation(Result)
if test:
    # 2. Получение новых площадок проекта
    DocProjectLocations = doc.ProjectLocations
    # 3. Фильтр лишней площадки
    fe_DocProjectLocations = []
    for DocProjectLocation in DocProjectLocations:
        if DocProjectLocation.Name in LinkProjectLocationsNames:
            fe_DocProjectLocations.append(DocProjectLocation)
    # 4. Запись положения в новые площадки
    count = 0
    for fe_DocProjectLocation in fe_DocProjectLocations:
        if fe_DocProjectLocation.Name == ListLinkProjectLocations[count].Name:
            Set_Position = ListLinkProjectLocations[count].GetProjectPosition(XYZ(0, 0, 0))
            fe_DocProjectLocation.SetProjectPosition(
                Set_Point,
                Set_Position
            )
            count += 1
    # 5. Вывод сообщения
    if count == len(ListLinkProjectLocations):
        OUT = "Всем площадкам были назначены координаты. Лишнюю площадку можно удалить вручную"
    else:
        OUT = "Площадок без правильного положения: " + str(len(ListLinkProjectLocations) - count)
else:
    OUT = "Площадки не созданы"
TransactionManager.Instance.TransactionTaskDone()

