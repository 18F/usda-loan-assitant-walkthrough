import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Union

from PyPDF2 import PdfFileReader

LOREM_IPSUM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque condimentum ullamcorper"
    " dolor eu molestie. Aliquam vulputate dui id fringilla malesuada. Morbi quis libero placerat,"
    " pulvinar diam tincidunt, bibendum turpis. Nullam malesuada lorem ut mattis ornare. Sed"
    " lacinia felis at dui vehicula, in imperdiet nulla varius. Phasellus a purus quis urna"
    " iaculis finibus. Donec eget dolor fringilla, posuere lacus vitae, sodales sapien. Nullam ac"
    " ex id odio lobortis aliquet."
)

USDA_FORM_DIR = "application"
USDA_FORMS = [
    "Form - AD1026.pdf",
    "Form - FSA2005 Creditor List.pdf",
    "Form - FSA2006.pdf",
    "Form - FSA2015 Verification of Debts and Assets.pdf",
    "FSA -2150 Development Plan.pdf",
    "FSA2001 Requst for Direct Loan Application (021022).pdf",
    "FSA 2002 with comments 2021.pdf",
    "FSA 2003 with Comments.pdf",
    "FSA2004 Authorization to Release Information.pdf",
    "FSA 2007 with comments.pdf",
    "FSA 2014 V of E with comments.pdf",
    "FSA2037 Farm Business Plan Worksheet.pdf",
    "FSA2038 FBPworksheet.pdf",
    "FSA 2301 Youth Loan.pdf",
    "FSA2302 Descript if Farm Training.pdf",
    "FSA2309_110120V02.pdf",
    "FSA 2310.pdf",
    "FSA 2314 Streamlined Request for Direct OL assistance with comments.pdf",
    "FSA2330 Microloan Application.pdf",
    "FSA 2370 Request for Waiver of Borrower Training with comments.pdf",
]


def get_form_id(reader: PdfFileReader) -> Optional[str]:
    """
    Helper method to extract the USDA Form ID from a given PDF file, if possible.

    :param reader: the PyPDF2 PdfFileReader that wraps the PDF contents
    :return: a string representing the form ID, starting with AD or FSA / None, otherwise
    """
    first_page = reader.pages[0]
    form_id = None
    if "/Contents" in first_page:
        page_content_text = first_page.extractText()
        page_content = page_content_text.split("\n")
        page_content = "".join(page_content)
        page_content = page_content.replace(" ", "")
        form_id = re.search("(?:AD|FSA)-[0-9]{4}", page_content).group()
    return form_id


def get_form_parts_template(reader: PdfFileReader) -> List[Dict[str, Union[str, Any]]]:
    """
    Helper method to generate a template for a given form's Parts for use
    within the USDA Loan Assistant.

    A heuristic of number of pages in the PDF is used for guessing how many
    templated sections will be necessary.

    :param reader: the PyPDF2 PdfFileReader that wraps the PDF contents
    :return: a list of dicts containing the necessary key/values for representing a form's parts
    """
    parts = []
    for _ in reader.pages:
        part = {"name": "", "title": "", "description": "", "items": []}
        parts.append(part)
    return parts


def get_comments(reader: PdfFileReader) -> List[Dict[str, Any]]:
    """
    Helper method to retrieve a list of all the comments provided on a given annotated
    form.

    :param reader: the PyPDF2 PdfFileReader that wraps the PDF contents
    :return: a list of dicts containing the comments and other necessary
        key/values for representing a single form item
    """
    comment_list = []

    for page in reader.pages:
        if "/Annots" in page:
            for annot in page["/Annots"]:
                subtype = annot.getObject()["/Subtype"]
                if subtype == "/Text":
                    obj = annot.getObject()
                    contents_obj = obj.get("/Contents")
                    if contents_obj:
                        content_entry = {"id": "", "name": ""}
                        contents = str(contents_obj).replace("\r", " ")
                        contents = contents.replace("\u2013", "-")
                        contents = contents.replace("\u2019", "'")
                        contents = contents.replace("\u201c", '"')
                        contents = contents.replace("\u201d", '"')
                        contents = contents.replace("\ufffd", "")
                        content_entry["comment"] = contents.strip()
                        comment_list.append(content_entry)

    return comment_list


def get_form_contents(pdf_file: str) -> Dict[str, Any]:
    """
    Helper method to generate a template dictionary for a single form, which can be parsed
    by the USDA Loan Assistant tool. The template corresponds to a single PDF file and contains
    as much information as can be parsed and pre-processed reasonably.

    :param pdf_file: a path to a PDF file containing a USDA form
    :return: a dict containing a templated representation of a USDA form
    """
    form_contents = {}
    reader = PdfFileReader(pdf_file)
    form_id = get_form_id(reader)
    form_contents["name"] = form_id
    form_contents["file_name"] = os.path.basename(pdf_file)
    form_contents["description"] = LOREM_IPSUM
    form_contents["parts"] = get_form_parts_template(reader)
    form_contents["parts"][0]["items"] = get_comments(reader)
    return form_contents


def main() -> None:
    """
    Driver method for this helper script. It will generate a templated JSON file for use
    with the USDA Loan Assistant tool.

    :return: None
    """
    if len(sys.argv) > 1:
        usda_form_dir = sys.argv[1]
    else:
        print(
            "The tool expects one argument of the form <path_to_usda_form_dir> where the path"
            " is relative to the current directory where the python call is made from,"
            " e.g. python comment_generator.py <path_to_usda_form_dir>"
        )
        sys.exit(1)

    content = {"Forms": []}
    for form in USDA_FORMS:
        form_path = os.path.join(usda_form_dir, form)
        form_contents = get_form_contents(form_path)
        content["Forms"].append(form_contents)

    # print(json.dumps(form_comments, indent=2))
    with open("comments.json", "w") as f:
        f.write(json.dumps(content, indent=2))


if __name__ == "__main__":
    main()
