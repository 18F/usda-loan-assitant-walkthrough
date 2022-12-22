import json
import shutil
import os
from time import sleep
from collections import defaultdict
#from pprint import pprint
from datetime import datetime
from pathlib import Path
from math import isnan
import click
from fuzzywuzzy import process
#from openpyxl import load_workbook
import pandas as pd
import numpy as np

import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords
stopwords = set(stopwords.words('english'))
from nltk.tokenize import word_tokenize
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager



LoanType = [
        {
            "type" : "annual",
            "forms" : ["FSA-2001", "FSA-2002", "FSA-2003", "FSA-2004", "FSA-2005", "FSA-2006", "FSA-2007", "FSA-2014", "FSA-2015", "FSA-2037", "FSA-2038", "FSA-2150", "FSA-2302", "FSA-2370", "FSA-851", "AD-1026"],
            "name": "Annual Operating Loans",
            "description": "Used for regular operating expenses and repaid within 12 months or when the commodities produced are sold",
            "image": "annual.jpg",
            "imageAltText": "A farmer smiling at the camera with rows of crops in the background"
        },
    
        {
            "type": "term",
            "forms": ["FSA-2001", "FSA-2002", "FSA-2003", "FSA-2004", "FSA-2005", "FSA-2006", "FSA-2007", "FSA-2014", "FSA-2015", "FSA-2037", "FSA-2038", "FSA-2150", "FSA-2302", "FSA-2370", "FSA-851", "AD-1026"],
            "name": "Term Operating Loans",
            "description": "Used to purchase livestock, seed, and equipment. Loan funds can also cover startup costs and family living expenses",
            "image": "term.jpg",
            "imageAltText": "A closeup on the face of a cow"
        },
    
        {
            "type": "ownership",
            "forms": ["FSA-2001", "FSA-2002", "FSA-2003", "FSA-2004", "FSA-2005", "FSA-2006", "FSA-2007", "FSA-2014", "FSA-2015", "FSA-2037", "FSA-2038", "FSA-2150", "FSA-2302", "FSA-2370", "FSA-851", "AD-1026"],
            "name": "Farm Ownership Loans",
            "description": "Used to purchase or expand a farm or ranch. Loan funds can be used for closing costs, construction, or conservation",
            "image": "ownership.jpg",
            "imageAltText": "Farmland featuring a barn and rows of crops"
        },
    
        {
            "type": "microloan",
            "forms": ["FSA-2330","AD-1026", "FSA-2014", "FSA-2037"],
            "name": "Microloans",
            "description": "Loans up to $50,000; used to meet the needs of small and beginning farmers or non-traditional specialty operations",
            "image": "micro.jpg",
            "imageAltText": "A farmer at a farmers market stall holding an OPEN for business sign"
        },
    
        {
            "type": "emergency",
            "forms": ["FSA-2001", "FSA-2002", "FSA-2003", "FSA-2004", "FSA-2005", "FSA-2006", "FSA-2007", "FSA-2014","FSA-2015", "FSA-2037", "FSA-2038", "FSA-2302", "FSA-2309", "FSA-2310", "FSA-2370", "AD-1026"],
            "name": "Emergency Loans",
            "description": "Used to restore damaged property due to a natural disaster; can cover production costs and family living expenses",
            "image": "emergency.jpg",
            "imageAltText": "A farm house destroyed by a fallen tree"
        },
    
        {
            "type": "youth",
            "forms": ["FSA-2301", "AD-1026"],
            "name": "Youth Loans",
            "description": "Used to help youth, ages 10 to 20, fund agricultural projects connected with educational programs like 4-H clubs or FFA",
            "image": "youth.jpg",
            "imageAltText": "A teenage girl on a farm holding a basket of produce"
        }
    ]


def find_matches( field_title, pdf_labels, verbose = False ):
    """Tries to match PDF-embedded form input instructions with
    LAT-enhanced instructions"""
    retval = process.extractOne( field_title, pdf_labels )
    if retval is not None:
        match, rate = retval
        if verbose:
            print( f'        --  closest match in PDF ({rate}%): "{match}"')
        if rate >= 75:
            return match
    return None


def Scrape_PDF_Input_Attrs( file_name, verbose=True, debug=True ):
    """Requires the web server to be running locally.
    Install Node.JS, then run `npm install http-server -g`, then cd into top level
    directory of this repo "usda-loan-assitant-walkthrough" and runn the command
    `http-server` which will then make the following URL valid:"""

    def Parse_CSS_Style( css_text : str ):
        return dict( _.strip().split( ': ' ) for _ in css_text.split( ';' ) if _ )

    url = "http://127.0.0.1:8080/js/pdfjs/web/viewer.html?file=/forms/"+file_name
    # Relevant HTML tag attribute names

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)

    # On some of the forms, there are no text widgets on page 1
    # which I believe causes the webdriver below to time out.
    # This isn't working right now:
    #driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    sleep_time = 10 # seconds
    print( "*"*80)
    print( "*"*80 )
    print( f"SLEEPING FOR {sleep_time} seconds, please scroll through open Selenium window TO EACH PAGE to ensure all the elements have been rendered, THEN scroll back to the top." )
    print( "*"*80)
    print( "*"*80 )
    sleep( sleep_time )

    try:
        # If input PDF document was created/edited using Adobe acrobat
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.textWidgetAnnotation")))
    except TimeoutException:
        # If input PDF document was created/edited using some other PDF
        # client, perhaps microsoft word
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.xfaTextfield")))

    descrip_to_pid_dict = {}

    if debug:
        # PIDs aggregated across all PDF pages:
        all_pid_data = defaultdict( list )
        # Contains uncombined text label parts across all pages and multiple spans:
        raw_text_data = defaultdict( list )

    # Step 1: grab all div's with class=page
    all_pdf_pages = driver.find_elements( By.CSS_SELECTOR, '.page' )

    if verbose:
        # At the form level
        # indent level = 2
        print( f'  In file "{file_name}" found {len( all_pdf_pages )} pages' )

    # Iterate over all pages
    for page_index, page_element in enumerate( all_pdf_pages ):

        if verbose:
            # At the page level
            # indent level = 4
            print( f'    Processing PDF page {page_index +1}' )

        page_number = page_element.get_attribute('data-page-number')
        # Page style contains the basic dimensions in pixels for width and height
        page_style = page_element.get_attribute('style')
        page_label = page_element.get_attribute('aria-label') or page_element.get_attribute('data-name')
        page_loaded = page_element.get_attribute('data-loaded')

        if not page_loaded:
            raise ValueError( f"Apparently, pdfJS did not load page {page_number}, did you get a chance to scroll to it in the Selenium browser window?" )

        # Step 2: Get the text box annotations and their coordinates within the page
        # Get the div element with class='textLayer'
        text_layer_div = page_element.find_elements( By.CSS_SELECTOR, '.textLayer' )
        if verbose:
            print( f'    On page {page_number} found {len( text_layer_div )} <div class="textLayer">' )
        if len( text_layer_div ) == 0:
            print( f'Skipping page {page_number} due to lack of "textLayer" elements' )
            continue

        assert len( text_layer_div ) == 1

        text_layer_div = text_layer_div[0]

        # text is grouped by pdfJS as span-with-spans
        # This happens when text has different font, italicized,
        # or apperas across multiple lines. The text needs to be combined.
        # This one houses the combined, curated text data
        text_data_this_page = defaultdict( list )

        markedContent_elements = text_layer_div.find_elements( By.XPATH, "span[@class='markedContent']" )
        if verbose:
            # At the page level
            # indent level = 4
            print( f'    On page {page_number} found {len( markedContent_elements )} <span class="markedContent">' )

        if len( markedContent_elements ) == 0:
            print( f'Skipping page {page_number} due to lack of "markedContent" elements' )
            continue

        for outer_span_element in markedContent_elements:

            span_id = outer_span_element.get_attribute( 'id' )

            presentation_elements = outer_span_element.find_elements( By.XPATH, "span[@role='presentation']" )
            if len( presentation_elements ) == 0:
                continue

            #elem_rect = { k : int( round( v ) ) for k,v in outer_span_element.rect.items() }

            if verbose:
                #print( f'      On page {page_number} in span "{span_id}" within bounding rect={elem_rect} found {len( presentation_elements )} text spans' )
                print( f'      On page {page_number} in span "{span_id}" found {len( presentation_elements )} text spans:' )

            texts = [ _.text.strip() for _ in presentation_elements ]
            text_lengths = [ len( _ ) for _ in texts ]
            total_text_length = sum( text_lengths )
            style_dicts = [ Parse_CSS_Style( _.get_attribute( 'style' ) ) for _ in presentation_elements ]
            xs = [ float( _['left'].replace( 'px', '' ) ) for _ in style_dicts ]
            ys = [ float( _['top'].replace( 'px', '' ) ) for _ in style_dicts ]

            # Compute weighted sum centroid based on the amount of text in the span
            centroid_x = int( round( sum( [ x * w for x, w in zip( xs, text_lengths ) ] ) / total_text_length ) )
            centroid_y = int( round( sum( [ y * w for y, w in zip( ys, text_lengths ) ] ) / total_text_length ) )
            combined_text = " ".join( texts )

            if verbose:
                print( f'        centroid=<x={centroid_x},y={centroid_y}>, combined text="{combined_text}"' )

            if debug:
                raw_text_data['page'].extend( [ page_number for i in range( len( texts ) ) ] )
                raw_text_data['span_id'].extend( [ span_id for i in range( len( texts ) ) ] )
                raw_text_data['centroid_x'].extend( [ centroid_x for i in range( len( texts ) ) ] )
                raw_text_data['centroid_y'].extend( [ centroid_y for i in range( len( texts ) ) ] )
                raw_text_data['x'].extend( xs )
                raw_text_data['y'].extend( ys )
                raw_text_data['text'].extend( texts )

            text_data_this_page['span_id'].append( span_id )
            text_data_this_page['x'].append( centroid_x )
            text_data_this_page['y'].append( centroid_y )
            text_data_this_page['text'].append( combined_text )

        text_data_this_page = pd.DataFrame( text_data_this_page )

        if len( text_data_this_page ) == 0:
            print( "    No text labels found on page {page_number}" )
            continue

        # Convert location to complex number to facilitate vectorized distance calculation
        # https://towardsdatascience.com/efficient-euclidean-distance-computation-in-pandas-66b472f6b0ba
        text_data_this_page['xy'] = text_data_this_page['x'] + text_data_this_page['y'] * 1j

        # Step 3: Now find all input and text areas wiithin the given page:
        inputs_on_this_page = page_element.find_elements( By.CSS_SELECTOR, 'input, textarea' )

        if verbose:
            # At the page level
            # indent level = 4
            print( f'    On page {page_number} found {len( inputs_on_this_page )} <input> and/or <textarea> elements' )

        for input_element in inputs_on_this_page:

            data_name_text = input_element.get_attribute('data-name')
            aria_label_text = input_element.get_attribute('aria-label')
            raw_description_text = data_name_text or aria_label_text
            pid = input_element.get_attribute('id')

            if not( raw_description_text and pid.endswith('R') ):
                continue

            elem_name = input_element.get_attribute( 'name' )
            elem_type = input_element.get_attribute( 'type' )
            elem_rect = { k : int( round( v ) ) for k,v in input_element.rect.items() }

            # Distance calculation option 1 of 3: Use Selenium-provided bounding box
            # Requires user to scroll back to the top and use modulus division
            # subtract the height of previous pages
            #x = elem_rect['x']
            #y = elem_rect['y'] * 1j
            # not implemented!

            parent_section_element = input_element.find_elements( By.XPATH, ".." )
            assert len( parent_section_element ) == 1
            parent_section_element = parent_section_element[0]
            assert parent_section_element.get_attribute( 'data-annotation-id' ) == pid

            parent_style = parent_section_element.get_attribute( 'style' )
            style_dict = Parse_CSS_Style( parent_style )

            # Distance calculation option 2 of 3: grab top and left location from
            # parent element's style attribute:
            x = float( style_dict['left'].replace( 'px', '' ) )
            y = float( style_dict['top'].replace( 'px', '' ) )
            topleft_coords = x + y * 1j
            topleft_distances = (text_data_this_page['xy'] - topleft_coords).abs()
            wanted_index = topleft_distances.idxmin()
            topleft_text_to_match = text_data_this_page.loc[ wanted_index, 'text' ]

            # Distance calculation option 3 of 3: additionally grab width
            # and height from parent style element and use it to find centroid of field
            #w = float( style_dict['width'].replace( 'px', '' ) )
            #h = float( style_dict['height'].replace( 'px', '' ) ) * 1j
            #centroid_coords = topleft_coords + w + h
            #centroid_distances = (text_data_this_page['xy'] - centroid_coords).abs()
            #wanted_index = centroid_distances.idxmin()
            #centroid_text_to_match = text_data_this_page.loc[ wanted_index, 'text' ]
            x_matched = text_data_this_page.loc[ wanted_index, 'x' ]
            y_matched = text_data_this_page.loc[ wanted_index, 'y' ]
            matched_span_id = text_data_this_page.loc[ wanted_index, 'span_id' ]

            #assert centroid_text_to_match == topleft_text_to_match, \
            #        f'centroid method ("{centroid_text_to_match}") != topleft method ("{topleft_text_to_match}")'

            if verbose:
                print( f'      Annotation top-left coord <x={x},y={y}> text: "{raw_description_text}"' )
                print( f'        Matched to coord <x={x_matched},y={y_matched}> span id="{matched_span_id}" text="{topleft_text_to_match}"' )

            stripped_description_text = \
                " ".join( [ _ for _ in word_tokenize( raw_description_text ) if _ not in stopwords ] )

            descrip_to_pid_dict[ stripped_description_text ] = {
                "id" : pid,
                "type" : elem_type,
                "data-name" : data_name_text,
                "aria-label" : aria_label_text,
                "raw_description_text" : raw_description_text,
                "selenium_rect" : elem_rect,
                "top" : y,
                "left" : x,
                "name" : elem_name,
                "distance_method_matched_text" : topleft_text_to_match
            }
            if debug:
                all_pid_data['page_number'].append( page_number )
                all_pid_data['page_style'].append( page_style )
                all_pid_data['page_label'].append( page_label )
                all_pid_data['page_loaded'].append( page_loaded )
                all_pid_data['id'].append( pid )
                all_pid_data['name'].append( elem_name )
                all_pid_data['type'].append( elem_type )
                all_pid_data['raw_desc_text'].append( raw_description_text )
                all_pid_data['stripped_desc_text'].append( stripped_description_text )
                all_pid_data['rect'].append( elem_rect )
                all_pid_data['distance_method_text'].append( topleft_text_to_match )

    if debug:
        output_debug_data_filepath = str( Path( file_name ).stem ) + "_scraped_input_elems.xlsx"
        df = pd.DataFrame( all_pid_data )
        if len( df ) > 0:
            new_col_names = [ 'height', 'width', 'x', 'y' ]
            df[ new_col_names ] = pd.json_normalize( df['rect'] )
            df = df.drop( columns=['rect'] )
            df[ 'page_width' ] = df['page_style'].str.extract( r'width: (\d+)px;')
            df[ 'page_height' ] = df['page_style'].str.extract( r'height: (\d+)px;')
            df = df.drop( columns=['page_style'] )
            df.to_excel( output_debug_data_filepath )

        output_debug_data_filepath = str( Path( file_name ).stem ) + "_scraped_text_annotation_locations.xlsx"
        df = pd.DataFrame( raw_text_data )
        if len( df ) > 0:
            df.to_excel( output_debug_data_filepath )

    return descrip_to_pid_dict

def Process_Forms_Spreadsheet(
        source_filename,
        specific_form_request,
        form_limit,
        field_limit,
        update_pids=False,
        verbose=False,
        debug=False
):

    if verbose:
        print( f"Loading {source_filename}" )

    #wb = load_workbook( filename = source_filename )

    input_excel_path_obj = Path( source_filename )

    if not input_excel_path_obj.exists():
        raise ValueError( f' File "{source_filename}" does not exist in curr working directory "{os.getcwd()}"' )

    if update_pids:
        output_excel_filepath = \
            input_excel_path_obj.stem + \
            "_updated_" + \
            datetime.strftime( datetime.now(), '%Y-%m-%d_%H:%M:%S' ) + \
            input_excel_path_obj.suffix

        # Make a copy of the file upon which to "overlay" new pids
        shutil.copy( input_excel_path_obj, output_excel_filepath )

        writer = pd.ExcelWriter( output_excel_filepath, mode='a', if_sheet_exists="overlay" )

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
        if running_form_count > form_limit:
            break

        #form_id = inventory_sheet["B" + str(row)].value
        if specific_form_request is not None and form_id != specific_form_request:
            continue

        if verbose:
            # indent level = 2
            print(f'  **  Processing form {form_id}')

        #file_name = inventory_sheet["C" + str(row)].value
        #items_sheet  = wb[form_id]
        items_sheet_df = pd.read_excel( io=source_filename, sheet_name=form_id )
        #last_items_row = len(list(items_sheet.rows))

        if verbose:
            # indent level = 2
            print(f'  **  Found {len(items_sheet_df)} row items on sheet "{form_id}" in file "{source_filename}"')

        items_sheet_df[ 'Field Label' ] = items_sheet_df[ 'Field Label' ].fillna( "" ).astype( str )
        items_sheet_df[ 'Field #' ] = items_sheet_df[ 'Field #' ].fillna( "" ).astype( str )

        # We will be updating this possibly empty float64 column with text
        # by creating views into this data frame and writing into those.
        # Override pandas default behavior which is to create a copy of the df if the
        # object being written (here, strings) is not the same type as the column
        # again, float64 if empty:
        items_sheet_df[ 'Input ID' ] = items_sheet_df[ 'Input ID' ].astype( str ).replace( 'nan', "" )

        items_sheet_df[ 'Field Label' ].apply(
            lambda desc: " ".join( [ _ for _ in word_tokenize( desc ) if _ not in stopwords ] )
            )

        if update_pids:
            form_inputs = Scrape_PDF_Input_Attrs( form_file_name, debug=debug )
            new_pdf_input_descriptions = form_inputs.keys()

        form_parts_df = parts_sheet_df[ parts_sheet_df['form_id'] == form_id ]
        #for part_row in range(2, last_parts_row + 1):

        if verbose:
            # indent level = 2
            print(f'  **  Found {len(form_parts_df)} form parts corresponding fo form "{form_id}" on sheet "Parts Inventory" in file "{source_filename}"')

        if len( form_parts_df ) == 0:
            raise ValueError( f'Please add form parts for form "{form_id}" on sheet "Parts Inventory" in file "{source_filename}"' )

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

            part_dict = {
                "name": part_name,
                #"title": parts_sheet["C"+str(part_row)].value,
                "title": "" if pd.isna(part_title) or not(part_title) else part_title,
                #"description": parts_sheet["D"+str(part_row)].value,
                "description": "" if pd.isna(part_description) or not(part_description) else part_description
            }

            running_field_count = 0
            #    for item_row in range(2, last_items_row + 1):

            #        if part_name == items_sheet["B"+str(item_row)].value:
            # Grab a view into this sheet:
            items_in_this_part_df = items_sheet_df[
                items_sheet_df[ 'Part' ] == part_name
            ]

            if verbose:
                # Indent level = 4
                print( (" "*4) +f'**  Found { len( items_in_this_part_df ) } rows corresponding to part {part_name} "{part_title}" on sheet "{form_id}" in file "{source_filename}"')

            if len( items_in_this_part_df ) == 0:
                raise ValueError( f'Please make sure any row items for part "{part_name}" on sheet "{form_id}" have the string "{part_name}" in the Part column (column B?), or delete the part on the "Part Inventory" sheet.' )

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
            # ('K', 'PDF Page #'),
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
                'PDF Page #', # Col K
                'Field Left (px)', # Col L
                'Field Top (px)', # Col M
            ]

            items_list = []
            # Iterate over all the input elements in this part:
            for index, (
                field_number, # Field #
                field_name,   # Field Label
                preexisting_pid, # Input ID
                new_instructions_text, # Recommended Field Instructions
                page_number, # Page #
                field_left_px, # Field Left (px)
                field_top_px # Field Top (px)
            ) in zip( items_in_this_part_df.index, items_in_this_part_df[ wanted_columns ].values ):

                running_field_count += 1
                if running_field_count > field_limit:
                    break

                # Skip if the field label is blank, as in Form 2015, Part A Field
                # or if the Excel spreadsheet is missing any of these items:
                if field_number == "" or field_name == "":# or isnan( field_left_px ) or isnan( field_top_px ):
                    if verbose:
                        print(f'      **  Skipping form="{form_id}", row item={index+1}, Part "{part_name}"' )
                    continue

                try:
                    # break out these string interpolations so you can know which cell is causing the problem
                    field_number_str = str( field_number )
                    pdf_page_str = str( int( page_number ))
                    label_str = str( field_name )

                    output = f'      ** form="{form_id}", row item={index+1}, part="{part_name}", field #="{field_number}", PDF page={int(page_number)}, label="{field_name}"'
                except Exception as e:
                    print( "\n\n\n" + "*"*50 )
                    print( "ERROR OCCURRED" )
                    print( f' Error processing line {index+1} on sheet "{form_id}", please make sure all the boxes in the row like "page number" aren\'t blank (can just use placeholder if necessary) or leave "Field #" (column C?) blank to skip the row entirely.' )

                    print( "\n\n\n" )
                    raise
                    #import sys
                    #sys.exit( 1 )

                if verbose:
                    # Indent level = 6
                    print( output )

                new_pid = ''
                if update_pids:
                    match = find_matches(
                        field_name,
                        new_pdf_input_descriptions,
                        verbose
                    )
                    if match:
                        new_pid = form_inputs[ match ][ 'id' ]
                        # Write it back into the sheet
                        items_sheet_df.loc[ index, "Input ID" ] = new_pid
                        print( " " * 8, f'match in PDF has left={form_inputs[ match ]["left"]} top={form_inputs[ match ]["top"]}' )
                else:
                    new_pid = preexisting_pid

                pid_list.append( new_pid )

                # Field number is a text field anyway
                item_id = "" if( isinstance( field_number, float) and isnan( field_number )) else str( field_number )
                item_dict = {
                    "id": item_id,
                    "name": field_name,
                    "comment": "" if pd.isna(new_instructions_text) or not(new_instructions_text) else new_instructions_text, 
                    "page": 0 if pd.isna(page_number) or not(page_number) else page_number,
                    "left": 0 if pd.isna(field_left_px) or not(field_left_px) else field_left_px,
                    "top": 0 if pd.isna(field_top_px) or not(field_top_px) else field_top_px,
                    "pid": "" if pd.isna(new_pid) or not(new_pid) else new_pid
                    }
                items_list.append(item_dict)

                # END of loop iterating over items in this part

            part_dict['items'] = items_list
            parts_list.append( part_dict )

            # END of loop iterating over all the parts in this form

        data["Forms"].append({
            "name": form_name or "",
            "id": form_id or "",
            "file_name": form_file_name or '',
            "url": "" if pd.isna(form_url) or not(form_url) else form_url,
            "description": "" if pd.isna(form_description) or not(form_description) else form_description,
            "parts": parts_list
        })

        if update_pids:

            outgoing_pid_series = items_sheet_df[ "Input ID" ]
            if verbose:
                print( f'  Count of all pids={ ( outgoing_pid_series != "" ).sum() }, Count of UNIQUE pids={ len( set( outgoing_pid_series ) ) }' )
            outgoing_pid_series.to_frame().to_excel(
                writer,
                sheet_name = form_id,
                # Input ID column is column G, the 6th if counting from 0:
                startcol = 6
            )

        if verbose:
            # indent level = 2
            print(f'  **  FINISHED processing form {form_id}\n', "*"*50, "\n" )

    #wb.save( output_excel_filepath )
    #wb.close()
    if update_pids:
        if verbose:
            print( f'Updating file "{output_excel_filepath}" with new pids.' )
        writer.close()
    return data

@click.command()
@click.option('--filename', '-f', type=click.Path(exists=True), show_default=True, default='FSA Forms Analysis.xlsx')
@click.option('--updatepids', '-u', is_flag=True, show_default=True, default=False)
@click.option('--verbose', '-v', is_flag=True, show_default=True, default=True)
@click.option('--debug', '-d', is_flag=True, show_default=True, default=True, help="Generate debug output files saved to disk when scraping PDFs" )
@click.option('--form', '-F', show_default=None, default=None)
@click.option('--form_limit', '-o', show_default=False, default=99999, help="(Deprecated) Run this script for only the first N forms listed in the spreadsheet" )
@click.option('--field_limit', '-i', show_default=False, default=99999,  help="(Deprecated) Run this script for only the first N fields for listed in the spreadsheet" )
def main(filename, updatepids, verbose, debug, form_limit, field_limit, form ):

    print( "filename =", filename)
    print( "updatepids =", updatepids )
    print( "verbose =", verbose )
    print( "debug =", debug )
    print( "form_limit =", form_limit )
    print( "field_limit =", field_limit )
    print( "form =", form )

    if verbose and form:
        print( "*" * 50, '\n', "only processing form with id =", form, "\n", "*" * 50 )
    forms_data = Process_Forms_Spreadsheet( filename, form, form_limit, field_limit, updatepids, verbose, debug )

    print("Creating JSON file")
    forms_data["LoanType"] = LoanType
    json_data = json.dumps(forms_data, sort_keys=True, indent=4)
    #if debug:
    #    pprint(json_data)
    filename = "forms.json."+datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S')+"_out"
    print(f"Saving output to {filename}")
    with open(filename, "w") as output:
        output.write(json_data)


if __name__ == "__main__":
    main()
