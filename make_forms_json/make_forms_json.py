import json
#from pprint import pprint
from datetime import datetime
from pathlib import Path
from math import isnan
import click
from fuzzywuzzy import process
from openpyxl import load_workbook
import pandas as pd

import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords
stopwords = set(stopwords.words('english'))
from nltk.tokenize import word_tokenize
#from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def find_matches( field_title, pdf_labels, verbose = False ):
    """Tries to match PDF-embedded form input instructions with
    LAT-enhanced instructions"""
    if verbose:
        print( f'        --  QUERY: "{field_title}"' )
    retval = process.extractOne( field_title, pdf_labels )
    if retval is not None:
        match, rate = retval
        if verbose:
            print( f'        --  closest match ({rate}%): "{match}"')
        if rate >= 75:
            return match
    return None


def Scrape_PDF_Input_Attrs(file_name):
    """Requires the web server to be running locally.
    Install Node.JS, then run `npm install http-server -g`, then cd into top level
    directory of this repo "usda-loan-assitant-walkthrough" and runn the command
    `http-server` which will then make the following URL valid:"""

    url = "http://127.0.0.1:8080/js/pdfjs/web/viewer.html?file=/forms/"+file_name
    # Relevant HTML tag attribute names

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
    descrip_to_pid_dict = {}

    print( "In", file_name, "found", len( all_pdf_form_inputs ), "elements:" )

    for input_element in all_pdf_form_inputs:

        data_name_text = input_element.get_attribute('data-name')
        aria_label_text = input_element.get_attribute('aria-label')
        raw_description_text = data_name_text or aria_label_text
        pid = input_element.get_attribute('id')

        if not( raw_description_text and pid.endswith('R') ):
            continue

        stripped_description_text = \
            " ".join( [ _ for _ in word_tokenize( raw_description_text ) if _ not in stopwords ] )

        descrip_to_pid_dict[ stripped_description_text ] = {
            "id" : pid,
            "type" : input_element.get_attribute( 'type' ),
            "data-name" : data_name_text,
            "aria-label" : aria_label_text,
            "raw_description_text" : raw_description_text
        }

    return descrip_to_pid_dict

def process_forms_spreadsheet(
        source_filename,
        specific_form_request,
        form_count,
        field_count,
        update_pids=False,
        verbose=False
):

    if verbose:
        print( f"Loading {source_filename}" )

    #wb = load_workbook( filename = source_filename )

    input_excel_path_obj = Path( source_filename )

    output_excel_filepath = \
        input_excel_path_obj.stem + \
        "_updated_" + \
        datetime.strftime( datetime.now(), '%Y-%m-%d_%H:%M:%S' ) + \
        input_excel_path_obj.suffix

    if verbose:
        print(f"Will write to output excel file { output_excel_filepath }")

    data = {}
    data["Forms"] = []

    #inventory_sheet = wb["Form Inventory"]
    form_sheet_df = pd.read_excel(
        io=source_filename,
        sheet_name="Form Inventory"
    )
    #last_forms_row = len(list(inventory_sheet.rows))

    #parts_sheet = wb["Part Inventory"]
    parts_sheet_df = pd.read_excel(
        io=source_filename,
        sheet_name="Part Inventory"
    )
    #last_parts_row = len(list(parts_sheet.rows))

    running_form_count = 0

    pid_list = []

    # iterate over all forms
    wanted_form_cols = [ 'name', 'id', 'file_name', 'url', 'description' ]
    for (
        form_name,
        form_id,
        form_file_name,
        form_url,
        form_description
    ) in form_sheet_df[ wanted_form_cols ].values:
    #for row in range(2, last_forms_row + 1):
        running_form_count += 1
        if running_form_count > form_count:
            break

        #form_id = inventory_sheet["B" + str(row)].value
        if specific_form_request is not None and form_id != specific_form_request:
            continue
        #file_name = inventory_sheet["C" + str(row)].value
        #items_sheet  = wb[form_id]
        items_sheet_df = pd.read_excel( io=source_filename, sheet_name=form_id )
        #last_items_row = len(list(items_sheet.rows))

        items_sheet_df[ 'Field Label' ].apply(
            lambda desc: " ".join( [ _ for _ in word_tokenize( desc ) if _ not in stopwords ] )
            )
        if verbose:
            # indent level = 2
            print(f' **  Processing form {form_id}')

        if update_pids:
            form_inputs = Scrape_PDF_Input_Attrs( form_file_name )
            new_pdf_input_descriptions = form_inputs.keys()

        form_parts_df = parts_sheet_df[ parts_sheet_df['form_id'] == form_id ]
        #for part_row in range(2, last_parts_row + 1):

        parts_list = []
        wanted_parts_cols = [ 'name', 'title', 'description' ]
        # Iterate over all the parts in the form
        for (
            part_name,
            part_title,
            part_description
        ) in form_parts_df[ wanted_parts_cols ].values:

            #part_name = parts_sheet["B"+str(part_row)].value

            #if parts_sheet["A"+str(part_row)].value == form_id:

            if verbose:
                # Indent level = 4
                print(f'   **  Processing part {part_name}')

            part_dict = {
                "name": part_name,
                #"title": parts_sheet["C"+str(part_row)].value,
                "title": part_title,
                #"description": parts_sheet["D"+str(part_row)].value,
                "description": part_description
            }

            running_field_count = 0
            #    for item_row in range(2, last_items_row + 1):

            #        if part_name == items_sheet["B"+str(item_row)].value:
            items_in_this_part_df = items_sheet_df[
                items_sheet_df[ 'Part' ] == part_name
            ]

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
                'Field #', # Col C
                'Field Label', # Col D
                'Input ID', # Col G
                'Recommended field instructions', # Col N
                'Page #', # Col K
                'Field Left (px)', # Col L
                'Field Top (px)', # Col M
            ]

            items_list = []
            # Iterate over all the input elements in this part:
            for (
                field_number,
                field_name,
                preexisting_pid,
                new_instructions_text,
                page_number,
                field_left_px,
                field_top_px
            ) in items_in_this_part_df[ wanted_columns ].values:

                running_field_count += 1
                if running_field_count > field_count:
                    break

                if verbose:
                    # Indent level = 6
                    print(f'     **  Processing form {form_id}, {part_name}, field {field_number}')

                new_pid = ''
                if update_pids:
                    match = find_matches(
                        field_name,
                        new_pdf_input_descriptions,
                        verbose
                    )
                    if match:
                        new_pid = form_inputs[ match ][ 'id' ]

                pid_list.append( new_pid )

                # Field number is a text field anyway
                item_id = "" if( isinstance( field_number, float) and isnan( field_number )) else str( field_number ),
                item_dict = {
                    "id": item_id,
                    "name": field_name,
                    "comment": new_instructions_text,
                    "page": page_number or 0,
                    "left": field_left_px or 0,
                    "top": field_top_px or 0,
                    "pid": new_pid
                }
                items_list.append(item_dict)

            # END iterating over items in this part
            part_dict['items'] = items_list
            parts_list.append( part_dict )

        # END iterating over all the parts
        data["Forms"].append({
            "name": form_name or "",
            "id": form_id or "",
            "file_name": form_file_name or '',
            "url": form_url or "",
            "description": form_description or "",
            "parts": parts_list
        })

    #wb.save( output_excel_filepath )
    #wb.close()
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
