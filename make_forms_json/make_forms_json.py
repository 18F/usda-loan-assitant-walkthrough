from openpyxl import load_workbook
import json
from datetime import datetime
import click
from fuzzywuzzy import process


from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


from pprint import pprint

def find_matches(field_title, pdf_labels):
    print(process.extractOne(field_title, pdf_labels))


def pdf_input_attrs(file_name):
        url = "http://127.0.0.1:8080/js/pdfjs/web/viewer.html?file=/forms/"+file_name
        INPUT_ATTR = ["id", "type","data-name", "aria-label"]
        print(url)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)

        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.textWidgetAnnotation")))
        except TimeoutException:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.xfaTextfield")))

        elements = driver.find_elements(By.CSS_SELECTOR, 'input, textarea')
        out = {}
        for el in elements:
            key = el.get_attribute('data-name') or el.get_attribute('aria-label')
            pid = el.get_attribute('id')
            if (key) and pid.endswith('R'):
                out[key] = {attr: el.get_attribute(attr) for attr in INPUT_ATTR}
        return out

def process_forms_spreadsheet(source_filename, form_count, field_count, update_pids=False, verbose=False, DEBUG=False):

    print(f"Loading {source_filename}")
    wb = load_workbook(filename = source_filename)
    

    data = {}
    data["Forms"] = []

    inventory_sheet = wb["Form Inventory"]
    last_forms_row = len(list(inventory_sheet.rows))

    parts_sheet = wb["Part Inventory"]
    last_parts_row = len(list(parts_sheet.rows))

    running_form_count = 0
    for row in range(2, last_forms_row + 1):
        
        running_form_count += 1 
        if running_form_count > form_count: break


        parts_list = []
        form_id = inventory_sheet["B" + str(row)].value
        file_name = inventory_sheet["C" + str(row)].value
        items_sheet  = wb[form_id]
        last_items_row = len(list(items_sheet.rows))
        
        if verbose:
            print(f' **  Processing form {form_id}')

        if update_pids:
            form_inputs = pdf_input_attrs(file_name)
            pdf_labels = form_inputs.keys()

        for part_row in range(2, last_parts_row + 1):

            part_name = parts_sheet["B"+str(part_row)].value

            if parts_sheet["A"+str(part_row)].value == form_id:

                if verbose:
                    print(f'   **  Processing part {part_name}')

                part_dict = {
                    "name": part_name,
                    "title": parts_sheet["C"+str(part_row)].value,
                    "description": parts_sheet["D"+str(part_row)].value,
                }

                items_list = []
                running_field_count = 0
                for item_row in range(2, last_items_row + 1):

                    if part_name == items_sheet["B"+str(item_row)].value:

                        running_field_count += 1
                        if running_field_count > field_count: break

                        field_name = items_sheet["D"+str(item_row)].value or ''


                        if verbose:
                            print(f'     **  Processing item {item_row}: {field_name}')

                        if update_pids:
                            matches = find_matches(field_name, pdf_labels)

                        item_id = items_sheet["C"+str(item_row)].value or ""
                        item_dict = {
                            "id": str(int(item_id)) if type(item_id) == float and item_id == int(item_id) else str(item_id),
                            "name": field_name,
                            "comment": items_sheet["N"+str(item_row)].value or '',
                            "page": items_sheet["K"+str(item_row)].value or 0,
                            "left": items_sheet["L"+str(item_row)].value or 0,
                            "top": items_sheet["M"+str(item_row)].value or 0,
                            "pid": items_sheet["G"+str(item_row)].value or ''
                        }
                        items_list.append(item_dict)

                part_dict['items'] = items_list
                parts_list.append(part_dict)

        data["Forms"].append({
            "name": inventory_sheet["A" + str(row)].value or '',
            "id": inventory_sheet["B" + str(row)].value or '',
            "file_name": file_name or '',
            "url": inventory_sheet["D" + str(row)].value or '',
            "description":  inventory_sheet["E" + str(row)].value or '',
            "parts": parts_list
        })


    wb.close()
    return(data)






@click.command()
@click.option('--filename', '-f', type=click.Path(exists=True), show_default=True, default='FSA Forms Analysis.xlsx')
@click.option('--updatepids', '-u', is_flag=True, show_default=True, default=False)
@click.option('--verbose', '-v', is_flag=True, show_default=True, default=False)
@click.option('--debug', '-d', is_flag=True, show_default=True, default=False)
@click.option('--form_count', '-o', show_default=False, default=99999)
@click.option('--field_count', '-i', show_default=False, default=99999)
def main(filename, updatepids, verbose, debug, form_count, field_count):
    forms_data = process_forms_spreadsheet(filename, form_count, field_count, updatepids, verbose)

    print("Creating JSON file")
    json_data = json.dumps(forms_data, sort_keys=True, indent=4)
    
    if debug:
        pprint(json_data)
    
    filename = "forms.json."+datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S')+"_out"
    print(f"Saving output to {filename}")
    with open(filename, "w") as output:
        output.write(json_data)


if __name__ == "__main__":
    main()
