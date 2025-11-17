# -*- coding: utf-8 -*-
#==================================================
#IMPORTS
#==================================================
from itertools import count
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import revit, UI, DB
from System.Collections.Generic import List
import re
import sys
import os
import clr
import re
import csv
from collections import defaultdict, OrderedDict
clr.AddReference('System.IO')
from datetime import datetime
from functions._CustomSelections import CustomSelections
# from System import Guid
# from System.Diagnostics import Stopwatch

#=== Time start
# sw = Stopwatch()
# sw.Start()
start_time = datetime.now()

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

doc = revit.doc

categories = [
    BuiltInCategory.OST_StructConnections,
    BuiltInCategory.OST_Rebar,
    BuiltInCategory.OST_PipeSegments,
    BuiltInCategory.OST_LoadCases,
    BuiltInCategory.OST_DetailComponents,
    BuiltInCategory.OST_EdgeSlab,
    BuiltInCategory.OST_SpecialityEquipment,
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_PlumbingFixtures,
    BuiltInCategory.OST_MechanicalEquipment,
    BuiltInCategory.OST_ElectricalFixtures,
    BuiltInCategory.OST_ElectricalEquipment,
    BuiltInCategory.OST_ShaftOpening,
    BuiltInCategory.OST_StairsLandings,
    BuiltInCategory.OST_StairsRuns,
    # BuiltInCategory.OST_Materials,
    BuiltInCategory.OST_Elev,
    BuiltInCategory.OST_CurtainGridsWall,
    BuiltInCategory.OST_Parts,
    BuiltInCategory.OST_SpotSlopes,
    BuiltInCategory.OST_WeakDims,
    BuiltInCategory.OST_PlanRegion,
    BuiltInCategory.OST_CurtainWallMullions,
    BuiltInCategory.OST_CurtainWallPanels,
    BuiltInCategory.OST_GenericModel,
    BuiltInCategory.OST_StairsRailingBaluster,
    BuiltInCategory.OST_StairsRailing,
    BuiltInCategory.OST_Stairs,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_Doors,
    BuiltInCategory.OST_Windows,
    BuiltInCategory.OST_Walls
]

#==================================================
#FUNCTIONS
#==================================================


def get_param_value(param):
    storage_type = param.StorageType
    try:
        if storage_type == StorageType.String:
            return param.AsValueString()
        elif storage_type == StorageType.Double:
            return param.AsDouble()
        elif storage_type == StorageType.Integer:
            if param.Definition.Name == 'Рабочий набор':
                return param.AsValueString()
            return param.AsInteger()
        elif storage_type == StorageType.ElementId:
            return param.AsValueString()
        else:
            val = param.AsValueString()
            return val if val is not None else ''
    except:
        return ''


def get_param_name(param):
    try:
        return param.Definition.Name
    except:
        return "Unknown"

#==================================================
#MAIN
#==================================================

#=== Отладка
# sel = CustomSelections(doc, uidoc)
# elements = sel.get_picked()
# data_rows = [] 
# all_param_keys = set()

# base_fields = ["ElementId", "Category"]
# for field in base_fields:
#     all_param_keys.add(field)

# # category_list = List[BuiltInCategory]()
# # for cat in categories:
# #     category_list.Add(cat)

# for el in elements:
#     cat_name = el.Category.Name
#     row = {}
#     row["ElementId"] = str(el.Id.IntegerValue)
#     row["Category"] = cat_name

#     #---Parameters type
#     element_type = doc.GetElement(el.GetTypeId())
#     print('Type------------------------------------------')
#     if element_type:
#         for param in element_type.Parameters:
#             name = get_param_name(param)
#             value = get_param_value(param)
#             row[name] = value
#             all_param_keys.add(name)
#             print("{} - {}".format(name, value))

#     print('Example------------------------------------------')
#     #---Parameters element    
#     for param in el.Parameters:
#         name = get_param_name(param)
#         value = get_param_value(param)
#         row[name] = value
#         all_param_keys.add(name)
#         print("{} - {}".format(name, value))
#     data_rows.append(row)



#=== Data collection 
data_rows = [] 
all_param_keys = set()

base_fields = ["ElementId", "Category"]
for field in base_fields:
    all_param_keys.add(field)

category_list = List[BuiltInCategory]()
for cat in categories:
    category_list.Add(cat)

# collector = FilteredElementCollector(doc)
# elements = collector.WherePasses(
#     ElementMulticategoryFilter(category_list)
#     ).ToElements()

print("Data collection has begun at {}".format(start_time))
# print(elements)
for cat in categories:
    print(cat)

    elements = FilteredElementCollector(doc).OfCategory(cat).ToElements()
    for el in elements:
        cat_name = el.Category.Name
        row = {}
        row["ElementId"] = str(el.Id.IntegerValue)
        row["Category"] = cat_name

        #---Parameters type
        element_type = doc.GetElement(el.GetTypeId())

        if element_type:
            for param in element_type.Parameters:
                name = get_param_name(param)
                # key = "Type_{}".format(name)
                row[name] = get_param_value(param)
                all_param_keys.add(name)

        
        #---Parameters element    
        for param in el.Parameters:
            name = get_param_name(param)
            #  key = "Instance_{}".format(name)
            row[name] = get_param_value(param)
            all_param_keys.add(name)
        data_rows.append(row)

# === All rows belong to the same set of columns
headers = sorted(all_param_keys)
csv_data = [headers]    

for row_dict in data_rows:
    full_row = []
    for key in headers:
        full_row.append(row_dict.get(key, ""))
    csv_data.append(full_row)

# === Writing to CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "revit_params_{}.csv".format("_".join(doc.Title.split('_')[:4])))

with open(output_path, 'a') as f:
    writer = csv.writer(f)
    for row in csv_data:
        encoded_row = []
        for cell in row:
            if isinstance(cell, unicode):
                encoded_row.append(cell.encode('utf-8'))
            else:
                encoded_row.append(str(cell) if cell is not None else "")
        writer.writerow(encoded_row)

end_time = datetime.now()
execution_time = end_time - start_time
# sw.Stop()
# print("Lead time: {}".format(sw.Elapsed))
print("export has been completed: {}".format(execution_time))
print("Total elements: {}, Total parameters: {}".format(len(data_rows), len(headers)))
