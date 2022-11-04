import json, sys
from  pprint import pprint
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def pdf_as_html(file_name):
    url = "http://127.0.0.1:8080/js/pdfjs/web/viewer.html?file=/forms/"+file_name

    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(url)
    try: 
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.textWidgetAnnotation")))
    except TimeoutException:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.xfaField")))

    return driver

def get_elements(form):
    INPUT_ATTR = ["id", "type","data-name", "aria-label"]
    
    elements = form.find_elements(By.CSS_SELECTOR, 'input, textarea')
    for el in elements:
        pprint( [el.get_attribute(attr) for attr in INPUT_ATTR] )
        


def main(forms_json = '../forms/forms.json'):
    print('Validating form PIDs')
    with open(forms_json) as f: 
        forms_data = json.load(f)

    for form_data in forms_data['Forms']:
        print(form_data["file_name"])
        form = pdf_as_html(form_data["file_name"])
        if form:
            
            print(len(form.find_elements(By.CSS_SELECTOR, 'input')))
        else:
            print("No Inputs?")
        
        get_elements(form)
        break
        # inputs = form.html.find('input')
        # pprint([(i.attrs.get("id"), i.attrs.get('data-name'), i.attrs.get('role')) for i in inputs])
        


if __name__ == '__main__':
    main()