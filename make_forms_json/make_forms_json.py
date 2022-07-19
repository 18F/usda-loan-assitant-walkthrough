from openpyxl import load_workbook
import json
from datetime import datetime

from pprint import pprint

source_filename = 'FSA Forms Analysis.xlsx'
print(f"Loading {source_filename}")
wb = load_workbook(filename = source_filename)


print("Creating JSON file")
data = {}
data["Forms"] = []

inventory_sheet = wb["Form Inventory"]
last_forms_row = len(list(inventory_sheet.rows))

parts_sheet = wb["Part Inventory"]
last_parts_row = len(list(parts_sheet.rows))

for row in range(2, last_forms_row + 1):

    parts_list = []
    form_id = inventory_sheet["B" + str(row)].value
    items_sheet  = wb[form_id]
    last_items_row = len(list(items_sheet.rows))

    for part_row in range(2, last_parts_row + 1):
        part_name = parts_sheet["B"+str(part_row)].value

        if parts_sheet["A"+str(part_row)].value == form_id:
            part_dict = {
                "name": part_name,
                "title": parts_sheet["C"+str(part_row)].value,
                "description": parts_sheet["D"+str(part_row)].value,
            }

            items_list = []
            for item_row in range(2, last_items_row + 1):
                # print(form_id, part_name, items_sheet["C"+str(item_row)].value)
                if part_name == items_sheet["B"+str(item_row)].value:
                    item_id = items_sheet["C"+str(item_row)].value
                    item_dict = {
                        "id": str(int(item_id)) if type(item_id) == float and item_id == int(item_id) else str(item_id),
                        "name": items_sheet["D"+str(item_row)].value,
                        "comment": items_sheet["M"+str(item_row)].value,
                        "page": items_sheet["J"+str(item_row)].value,
                        "left": items_sheet["K"+str(item_row)].value,
                        "top": items_sheet["L"+str(item_row)].value
                    }
                    items_list.append(item_dict)

            part_dict['items'] = items_list
            parts_list.append(part_dict)

    data["Forms"].append({
        "name": inventory_sheet["A" + str(row)].value,
        "id": inventory_sheet["B" + str(row)].value,
        "file_name": inventory_sheet["C" + str(row)].value,
        "url": inventory_sheet["D" + str(row)].value,
        "description":  inventory_sheet["E" + str(row)].value,
        "parts": parts_list
    })


# pprint(data)

# FSA2002 = next((item for item in data["Forms"] if item["id"] == "FSA-2002"), None)
# pprint(FSA2002)

wb.close()


json_data = json.dumps(data, sort_keys=True, indent=4)
# print(json_data)
filename = "forms.json."+datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S')+"_out"
print(f"Saving output to {filename}")
with open(filename, "w") as output:
    output.write(json_data)

