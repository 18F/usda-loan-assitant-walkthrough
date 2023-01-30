# Updating LAT forms JSON when PDFs change

The purpose of this script is to programmatically scrape USDA Farm Loan application PDF forms to obtain unique identifiers ("PIDs") for every text input box and input area. The output is a Microsoft Excel file that contains a row for every box. This can then be used as a basis for updating the tool tips that appear in the LAT tool gives the user helpful guidance as they are filling out the form. The output of this script should be merged back into the file "FSA Forms Analysis.xlsx" and the tool tip JSON can be regenerated. 

## Step 1: Install Prerequisites
1. Fire up the "Software Center" from your OCIO Help app within the "Self-Service" tab
2. Install the following software
    1. Python (version 3.10 as of 2023-01-30)
    2. Java 8 (64-bit)
    3. Node.js (v18.10.0 as of 2023-01-30)
    4. Git
3. Open up Windows PowerShell. Make sure the prereqs from step 1 above installed by running the commands and making sure they execute without errors
    1. ```Get-Command python```
    2. ```Get-Command node``` 
    3. ```Get-Command npm```
    4. ```Get-Command java```

## Step 2: Get this code if you haven't gotten it already
1. With your open Windows PowerShell, change directory to a convenient writable directory using the ```cd``` command or make a new one using ```mkdir``` command
2. Run command ```git clone https://github.com/18F/usda-loan-assitant-walkthrough.git```
3. Change directory into the newly downloaded code ```cd usda-loan-assitant-walkthrough```. This is the directory I will henceforth refer to in this documentation as $LAT_HOME.

## Step 3: Install 3rd party packages and start http server
1. With your open Windows PowerShell, change directory into $LAT_HOME using the ```cd``` command
2. Install Python prerequisites
    1. Run command ```python -m pip install nltk openpyxl pandas selenium click webdriver_manager```
3. Install Node prerequisites LOCALLY
    1. Run command ```npm install http-server --force --loglevel verbose```
    2. Verify that a new set of directories was installed, and verify there there is a node js script in with the path ```.\node_modules\http-server\bin\http-server```
    3. Run that script with the command ```node .\node_modules\http-server\bin\http-server```
    4. Ignore the error message that pops up. check that the http server is active by opening up any of your web browsers visiting the address ```http://127.0.0.1:8080```. The LAT website should appear.

## Step 4: Install your newly updated PDF form
1. Move your new form into the directory $LAT_HOME\forms
2. Edit the file $LAT_HOME\utils\data\FSA Forms Analysis.xlsx. On the "Form Inventory" spreadsheet, make sure the name and path of the newly updated form is represented in Column C "file_name".

## Step 5: Run make_forms_json_read_pids.py
1. With your open Windows PowerShell in the directory into $LAT_HOME, run the command ```python .\utils\python\make_forms_json\make_forms_json_read_pids.py --help``` to see all the command line options and to make sure you've installed all the necessary prerequisites
2. Run the command ```python .\utils\python\make_forms_json\make_forms_json_read_pids.py --help```
3. To scrape a single new PDF for its entity ids, run the command ```python .\utils\python\make_forms_json\make_forms_json_read_pids.py -F <form id> -u --debug```, where ```<form-id>``` is the identifier listed in FSA Forms Analysis.xlsx on the "Form Inventory" spreadsheet in the "id" column (column b)
    1. For example, ```python .\utils\python\make_forms_json\make_forms_json_read_pids.py -F FSA-2001-new -u --debug```

