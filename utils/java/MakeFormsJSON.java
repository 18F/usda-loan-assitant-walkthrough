import java.io.File;  
import java.io.FileWriter;
import java.io.FileReader;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;  
import java.util.Iterator; 
import java.util.Calendar;
import java.text.SimpleDateFormat;
import java.nio.charset.UnsupportedCharsetException;

import org.apache.poi.ss.usermodel.Cell;  
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.CellType;
import org.apache.poi.ss.util.CellReference;
import org.apache.poi.xssf.usermodel.*;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;



/* README:

This script converts the forms spreadsheet into a JSON file readable by 
the Loan Assistance tool website. 

To Build: In the script folder run: javac MakeFormsJSON.java -cp "./lib/*"
To Run: java -cp "./lib/*:."  MakeFormsJSON [XLSX File Name: ../../data/FSA Forms Analysis.xlsx]

The Script will recognize one positional command line argument for the
path of the XLSX file for the quiz content.  Without any input the 
script will assume the path .../../data/FSA Forms Analysis.xlsx by default.

*/

public class MakeFormsJSON {

    public static final String DATE_FORMAT_NOW = "yyyy-MM-dd_HHmmss";

    public static String now() {
        Calendar cal = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat(DATE_FORMAT_NOW);
        return sdf.format(cal.getTime());
    }


    public static XSSFSheet getSheetOrDie(XSSFWorkbook workbook, String sheet_name){
        // A wrapper around the getSheet by name method of poi.XSSF 
        // that will kill the script is the sheet is missing.

        XSSFSheet sheet = workbook.getSheet(sheet_name);
        if (sheet == null){
            System.out.println("Could nto find sheet "+sheet_name+" in the Forms XSLX. It is malformed.");
            System.exit(-1);
        }
        return sheet;
    }


    public static enum getCellValue {
        IntegerType, DoubleType, StringType, BooleanType; 

        @SuppressWarnings("unchecked")
        public static <T> T comeback(XSSFSheet sheet, String cellAddress) {
            CellReference cellReference = new CellReference(cellAddress); 
            Row row = sheet.getRow(cellReference.getRow());
            Cell cell = row.getCell(cellReference.getCol()); 

            if (cell == null){
                return (T) String.valueOf("");
            }
            
            switch (cell.getCellType()){
                case STRING:
                    return (T) String.valueOf(cell.getStringCellValue());
                case NUMERIC:
                    Double doubleValue = cell.getNumericCellValue();
                    if ((doubleValue % 1) == 0) {
                        return (T) Integer.valueOf(doubleValue.intValue());
                    } else {
                        return (T) Double.valueOf(doubleValue);
                    }
                case BLANK:
                    return (T) String.valueOf("");
                case BOOLEAN:
                    return (T) Boolean.valueOf(cell.getBooleanCellValue());
                default:
                    return (T) String.valueOf(cell.getStringCellValue());
            }
        }
    }

    public static String getCellValueString(XSSFSheet sheet, String cellAddress) { 
        CellReference cellReference = new CellReference(cellAddress); 
        Row row = sheet.getRow(cellReference.getRow());
        Cell cell = row.getCell(cellReference.getCol()); 

        switch (cell.getCellType()){
            case STRING:
                return cell.getStringCellValue();
            case NUMERIC:
                Double doubleValue = cell.getNumericCellValue();
                if ((doubleValue % 1) == 0) {
                    int cellValue = doubleValue.intValue();
                    return String.valueOf(cellValue);
                } else {
                    return String.valueOf(doubleValue);
                }
            case BLANK:
                return "";
            case BOOLEAN:
                return String.valueOf(cell.getBooleanCellValue());
            default:
                return cell.getStringCellValue();
        }
    }

    public static JSONArray getLoanTypes(){
        // Loan Types ar assumed to be stores in the same folder in a JSON
        // file called ./LoanTypes.json
        return getLoanTypes("../data/LoanTypes.json");
    }

    public static JSONArray getLoanTypes(String loan_types_file_path){
        // Get the loan Types from a loan types json file in the following format:
        // { <LoanType Object>
        // "LoanTypes":[ <Array of Objects in the following format>
        //     {
        //         "type" : "<String>",
        //         "forms" : [<Array of String Forms IDs>],
        //         "name": "<String>",
        //         "description": "<String>",
        //         "image": "<String: File path>",
        //         "imageAltText": "<String>",
        //     },
        //     .....
        //     ]
        // }

        
        try {
            JSONParser parser = new JSONParser();
            FileReader loan_types_reader = new FileReader(loan_types_file_path);
            Object loan_types_object = parser.parse(loan_types_reader);
            JSONObject loanTypeJsonObject = (JSONObject) loan_types_object;
            JSONArray loanTypeJsonArray = (JSONArray) loanTypeJsonObject.get("LoanTypes");
            return loanTypeJsonArray;

        } catch (FileNotFoundException e) {
            System.out.println("Loan Types JSON File "+loan_types_file_path+" was not found");
            System.exit(-1);
        } catch (IOException e) {
            System.out.println("Could not read Loan Types JSON File "+loan_types_file_path);
            System.exit(-1);
        } catch (ParseException e) {
            System.out.println("File "+loan_types_file_path+" was not a properly format JSON file");
            System.exit(-1);
        } catch (UnsupportedCharsetException e) {
            System.out.println("Charset UTF-8 is not supported on this system");
            System.exit(-1);
        }
        System.out.println("Could not parse Loan Types file.");
        System.exit(-1);
        return new JSONArray();
    }

    @SuppressWarnings("unchecked")
    public static void main(String[ ] args) { 
       
        String src_file_name;
        XSSFWorkbook workbook = null;
        
        // Get file name if provided or default to ./FSA Forms Analysis.xlsx
        if (args.length == 0){
            src_file_name = "../data/FSA Forms Analysis.xlsx";
        }else{
            src_file_name = args[0];
        }


        // Load the XSLX file 

        System.out.println("Attempting to load "+src_file_name);

        try {
            FileInputStream file = new FileInputStream(new File(src_file_name));
            System.out.println("Loaded "+src_file_name);
            workbook = new XSSFWorkbook(file);
            System.out.println("Loaded Workbook");
        } catch (FileNotFoundException e) {
            System.out.println("File "+src_file_name+" was not found");
            System.exit(-1);
        } catch (IOException e) {
            System.out.println("File "+src_file_name+" was not a properly format XSLX file");
            System.exit(-1);
        }

        XSSFSheet form_inventory_sheet = getSheetOrDie(workbook, "Form Inventory");
        XSSFSheet parts_inventory_sheet = getSheetOrDie(workbook,"Part Inventory");

        System.out.println("Iterating though the rows in  Sheet "+form_inventory_sheet.getSheetName());
        

        JSONObject json_data = new JSONObject();
        JSONArray forms_array =  new JSONArray();

        // Iterate through the form inventory sheet to collect form data 
        Iterator<Row> FormRowIterator = form_inventory_sheet.iterator();
        while (FormRowIterator.hasNext()){
            Row form_row = FormRowIterator.next();

            // The Iterator seems to index the lines, not number them so we will use 
            // the rel row num as row.getRowNum()  + 1

            int form_row_num = form_row.getRowNum() +1;

            // Skipping rows 
            if (form_row_num < 2){continue;} // Skip the headers
            // Skip all rows without a form name, stored in column A
            Cell test_cell = form_row.getCell(0); 
            if(test_cell == null){continue;}
            if(test_cell.getCellType() == CellType.BLANK){continue;}

            System.out.println(" * Processing Row "+ (form_row_num) + " - Form: " + test_cell.getStringCellValue());

            JSONObject form_object = new JSONObject();
            String form_id = getCellValue.comeback(form_inventory_sheet, "B"+(form_row_num));

            form_object.put("name", getCellValue.comeback(form_inventory_sheet, "A"+(form_row_num)));
            form_object.put("id", form_id);
            form_object.put("file_name", getCellValue.comeback(form_inventory_sheet, "C"+(form_row_num)));
            form_object.put("url", getCellValue.comeback(form_inventory_sheet, "D"+(form_row_num)));
            form_object.put("description", getCellValue.comeback(form_inventory_sheet, "E"+(form_row_num)));

            XSSFSheet form_fields_sheet = getSheetOrDie(workbook, form_id);
            System.out.println("  **  Found fields sheet");

            JSONArray forms_parts = new JSONArray();

            // Iterate through the parts inventory sheet to collect form parts data 
            Iterator<Row> PartsRowIterator = parts_inventory_sheet.iterator();
            while (PartsRowIterator.hasNext()){
                Row parts_row = PartsRowIterator.next();

                // The Iterator seems to index the lines, not number them so we will use 
                // the rel row num as row.getRowNum()  + 1

                int parts_row_num = parts_row.getRowNum() +1;

                // Skipping rows
                Cell parts_form_id_cell = parts_row.getCell(0); 
                // Skip rows without a part
                if(parts_form_id_cell == null){continue;}
                if(parts_form_id_cell.getCellType() == CellType.BLANK){continue;}
                // Skip parts of other forms
                String parts_form_id = parts_form_id_cell.getStringCellValue();
                if (parts_form_id != form_id){
                    continue;
                }

                String part_name = getCellValueString(parts_inventory_sheet, "B"+(parts_row_num));
                System.out.println("  **  Processing Part "+ part_name);

                JSONObject form_part = new JSONObject();
                form_part.put("name", part_name);
                form_part.put("title", getCellValue.comeback(parts_inventory_sheet, "C"+(parts_row_num)));
                form_part.put("description", getCellValue.comeback(parts_inventory_sheet, "D"+(parts_row_num)));

                JSONArray part_fields_array = new JSONArray();

                // Iterate through the  inventory sheet to collect form parts data 
                Iterator<Row> FieldRowIterator = form_fields_sheet.iterator();
                while (FieldRowIterator.hasNext()){
                    Row field_row = FieldRowIterator.next();

                    // The Iterator seems to index the lines, not number them so we will use 
                    // the rel row num as row.getRowNum()  + 1

                    int field_row_num = field_row.getRowNum() +1;

                    // Skipping rows 
                    if (field_row_num < 2){continue;} // Skip the headers
                    // Skip all rows without a field Id, stored in column A
                    Cell field_part_name_cell = field_row.getCell(1); 
                    if(field_part_name_cell == null){continue;}
                    if(field_part_name_cell.getCellType() == CellType.BLANK){continue;}
                    // Skip parts of other forms
                    String field_parts_name = field_part_name_cell.getStringCellValue();
                    if (field_parts_name != part_name){
                        continue;
                    }

                    JSONObject part_field = new JSONObject();

                    part_field.put("id", getCellValue.comeback(form_fields_sheet, "C"+(field_row_num)));
                    part_field.put("name", getCellValue.comeback(form_fields_sheet, "D"+(field_row_num)));
                    part_field.put("comment", getCellValue.comeback(form_fields_sheet, "N"+(field_row_num)));
                    part_field.put("page", getCellValue.comeback(form_fields_sheet, "K"+(field_row_num)));
                    part_field.put("left", getCellValue.comeback(form_fields_sheet, "L"+(field_row_num)));
                    part_field.put("top", getCellValue.comeback(form_fields_sheet, "M"+(field_row_num)));
                    part_field.put("pid", getCellValue.comeback(form_fields_sheet, "G"+(field_row_num)));

                    part_fields_array.add(part_field);

                }        

                form_part.put("items", part_fields_array);

                forms_parts.add(form_part);

            }

            form_object.put("parts", forms_parts);

            forms_array.add(form_object);

        }

        // Load the Loan Type Json file in a JSON Array
        // These will be added to the output JSON file at the end of the process.
        JSONArray LoanTypes = getLoanTypes();


        json_data.put("Forms", forms_array);
        json_data.put("LoanType", LoanTypes);
        
        
        // Ugly hack to undo the hardwired string escaping in JSON simple :(
        String json_string = json_data.toJSONString();//.replace("\\","");

        // System.out.println(json_string);

        String timestamp = now();
        String out_file_name = "./forms.json."+timestamp+"_out";

        System.out.println("Finished processing "+src_file_name);
        System.out.println("Writing JSON to  "+out_file_name);

        try {
            
            FileWriter forms_json_file = new FileWriter(out_file_name);
            forms_json_file.write(json_string);
            forms_json_file.close();
            System.out.println("Wrote "+out_file_name+" successfully");

          } catch (IOException e) {
            System.out.println("An error occurred while writing "+out_file_name);
            e.printStackTrace();
          }


        try {
            workbook.close();
        } catch (IOException e) {
            System.out.println("Could not close workbook...");
            System.exit(-1);
        }
        
    }
}


