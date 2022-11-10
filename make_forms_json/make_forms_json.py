import json
from pprint import pprint
from datetime import datetime
from pathlib import Path
import click
from fuzzywuzzy import process
from openpyxl import load_workbook
import pandas as pd

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def find_matches(field_title, pdf_labels, verbose = False):
    retval = process.extractOne(field_title, pdf_labels)
    if retval is not None:
        match, rate = retval
        if rate >= 75:
            if verbose:
                print("        --  NEW match: ", match, rate)
            return match
    return None


def Get_PDF_Input_Attrs(file_name):
    """Requires the web server to be running locally.
    Install Node.JS, then run `npm install http-server -g`, then cd into top level
    directory of this repo "usda-loan-assitant-walkthrough" and runn the command
    `http-server` which will then make the following URL valid:"""

    url = "http://127.0.0.1:8080/js/pdfjs/web/viewer.html?file=/forms/"+file_name
    # Relevant HTML tag attribute names
    wanted_attributes = ["id", "type", "data-name", "aria-label"]

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)

    # On some of the forms, there are no text widgets on page 1
    # which I believe causes the webdriver below to time out.
    # This isn't working right now:
    #driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    try:
        # If input PDF document was created/edited using Adobe acrobat
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.textWidgetAnnotation")))
    except TimeoutException:
        # If input PDF document was created/edited using some other PDF
        # client, perhaps microsoft word
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.xfaTextfield")))

    all_pdf_form_inputs = driver.find_elements( By.CSS_SELECTOR, 'input, textarea' )
    raw_descrip_to_pid_dict = {}
    print( "In", file_name, "found", len( pdf_form_inputs ), "elements:" )
    for input_element in all_pdf_form_inputs:
        description_text = input_element.get_attribute('data-name') or input_element.get_attribute('aria-label')
        pid = input_element.get_attribute('id')
        if description_text and pid.endswith('R'):
            raw_descrip_to_pid_dict[ description_text ] = \
                { attr_name: input_element.get_attribute( attr_name ) for attr_name in wanted_attributes }

    def StripStopwords( desc_text : str ) -> str:
        return " ".join( [ _ for _ in word_tokenize( desc_text ) if _ not in stopwords ] )

    stripped_descrip_to_pid_dict = \
        { StripStopwords( desc_text ) : pid for desc_text, pid in raw_descrip_to_pd_dict.items() }

    return raw_descrip_to_pid_dict, stripped_descrip_to_pid_dict

def process_forms_spreadsheet(source_filename, specific_form_request, form_count, field_count, update_pids=False, verbose=False):

    if verbose:
        print(f"Loading {source_filename}")
    wb = load_workbook(filename = source_filename)

    input_excel_path_obj = Path( source_filename )
    output_excel_filepath = input_excel_path_obj.stem + \
        "_updated_" + datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S') + \
        input_excel_path_obj.suffix

    if verbose:
        print(f"Will write to output excel file { output_excel_filepath }")

    data = {}
    data["Forms"] = []

    #inventory_sheet = wb["Form Inventory"]
    inventory_sheet_df = pd.read_excel( io=source_filename, sheet_name="Form Inventory" )
    #last_forms_row = len(list(inventory_sheet.rows))

    #parts_sheet = wb["Part Inventory"]
    parts_sheet_df = pd.read_excel( io=source_filename, sheet_name="Part Inventory" )
    #last_parts_row = len(list(parts_sheet.rows))

    running_form_count = 0
    # iterate over all forms
    for form_id, form_file_name in inventory_sheet[ ['id','file_name'] ].values:
    #for row in range(2, last_forms_row + 1):
        running_form_count += 1
        if running_form_count > form_count:
            break

        #parts_list = []
        #form_id = inventory_sheet["B" + str(row)].value
        if specific_form_request is not None and curr_form_id != specific_form_request:
            continue
        #file_name = inventory_sheet["C" + str(row)].value
        #items_sheet  = wb[form_id]
        items_sheet_df = pd.read_excel( io=source_filename, sheet_name=form_id )
        #last_items_row = len(list(items_sheet.rows))

        if verbose:
            print(f' **  Processing form {form_id}')

        if update_pids:
            raw_form_inputs, stripped_form_inputs = Get_PDF_Input_Attrs( file_name )
            pdf_labels = form_inputs.keys()

        form_parts_df = parts_sheet_df[ parts_sheet_df['form_id'] == form_id ]
        #for part_row in range(2, last_parts_row + 1):

        # split out the columns into their own lists
        for part_name, part_title, part_description in form_parts_df[ [ 'name', 'title', 'description' ] ].values:


            #part_name = parts_sheet["B"+str(part_row)].value

            #if parts_sheet["A"+str(part_row)].value == form_id:

            if verbose:
                print(f'   **  Processing part {part_name}')

            part_dict = {
                "name": part_name,
                #"title": parts_sheet["C"+str(part_row)].value,
                "title": part_title,
                #"description": parts_sheet["D"+str(part_row)].value,
                "description": part_description
            }

            #    #items_list = []
            running_field_count = 0
            #    for item_row in range(2, last_items_row + 1):

            #        if part_name == items_sheet["B"+str(item_row)].value:
            items_in_this_part_df = items_sheet_df[ items_sheet_df[ 'Part' ] == part_name ]

            #[('A', 'PART NAME'),
            # ('B', 'Part'),
            # ('C', 'Field #'),
            # ('D', 'Field Label'),
            # ('E', 'Original Field Instructions'),
            # ('F', 'Field Type'),
            # ('G', 'Input ID'),
            # ('H', 'Field Count'),
            # ('I', 'Validation'),
            # ('J', 'Length Limit'),
            # ('K', 'Page #'),
            # ('L', 'Field Left (px)'),
            # ('M', 'Field Top (px)'),
            # ('N', 'Recommended field instructions'),
            # ('O', 'Recommended Validation Rule'),
            # ('P', 'Error Message'),
            # ('Q', 'Data Entry Software Application')]

            wanted_columns = [
                'Field Label',
                'Field #',
                'Input ID',
                'Recommended field instructions',
                'Page #',
                '
            for field_name,  in items_in_this_part.itertuples():

                running_field_count += 1
                if running_field_count > field_count:
                    break

                field_name = getattr( item_row_data, #items_sheet["D"+str(item_row)].value or ''

                        if verbose:
                            print(f'     **  Processing item {item_row}: {field_name}')

                        if update_pids:
                            match = find_matches(field_name, pdf_labels, verbose)
                            if match:
                                if verbose:
                                    print( "          --  ORIGINAL:", form_inputs[match] )
                                new_pid = form_inputs[match]['id']
                                items_sheet["G"+str(item_row)].value = new_pid
                            else:
                                new_pid = ''

                        item_id = items_sheet["C"+str(item_row)].value or ""
                        item_dict = {
                            "id": str(int(item_id)) if isinstance(item_id, float) and item_id == int(item_id) else str(item_id),
                            "name": field_name,
                            "comment": items_sheet["N"+str(item_row)].value or '',
                            "page": items_sheet["K"+str(item_row)].value or 0,
                            "left": items_sheet["L"+str(item_row)].value or 0,
                            "top": items_sheet["M"+str(item_row)].value or 0,
                            # coletta edit: worksheet not updated until wb.save() is called
                            # which takes a really long time.
                            #"pid": items_sheet["G"+str(item_row)].value or ''
                            "pid": new_pid
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

    wb.save( output_excel_filepath )
    wb.close()
    return data

@click.command()
@click.option('--filename', '-f', type=click.Path(exists=True), show_default=True, default='FSA Forms Analysis.xlsx')
@click.option('--updatepids', '-u', is_flag=True, show_default=True, default=False)
@click.option('--verbose', '-v', is_flag=True, show_default=True, default=False)
@click.option('--debug', '-d', is_flag=True, show_default=True, default=False)
@click.option('--form', '-F', show_default=None, default=None)
@click.option('--form_count', '-o', show_default=False, default=99999)
@click.option('--field_count', '-i', show_default=False, default=99999)
def main(filename, updatepids, verbose, debug, form_count, field_count, form ):

    if verbose and form:
        print( "*" * 50, '\n', "only processing form with id =", form, "\n", "*" * 50 )
    forms_data = process_forms_spreadsheet(filename, form, form_count, field_count, updatepids, verbose)

    print("Creating JSON file")
    json_data = json.dumps(forms_data, sort_keys=True, indent=4)
    #if debug:
    #    pprint(json_data)
    filename = "forms.json."+datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S')+"_out"
    print(f"Saving output to {filename}")
    with open(filename, "w") as output:
        output.write(json_data)


if __name__ == "__main__":
    main()
