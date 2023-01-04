import java.io.File;  
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.FileNotFoundException;
import java.io.IOException;  
import java.util.Iterator; 
import java.util.Calendar;
import java.text.SimpleDateFormat;

import org.apache.poi.ss.usermodel.Cell;  
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.CellType;
import org.apache.poi.ss.util.CellReference;
import org.apache.poi.xssf.usermodel.*;

import org.json.simple.JSONObject;
import org.json.simple.JSONArray;

/* README:

This script converts the quiz spreadsheet into a JSON file readable by 
the Loan Assistance tool website. 

To Build: In the script folder run: javac MakeQuizJSON.java -cp "./lib/*"
To Run: java -cp "./lib/*:."  MakeQuizJSON [XLSX File Name: ./LAT-quiz-content.xlsx]

The Script will recognize one positional command line argument for the
path of the XLSX file for the quiz content.  Without any input the 
script will assume the path ./LAT-quiz-content.xlsx by default.

*/

public class MakeQuizJSON {

    public static final String DATE_FORMAT_NOW = "yyyy-MM-dd_HHmmss";

    public static String now() {
        Calendar cal = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat(DATE_FORMAT_NOW);
        return sdf.format(cal.getTime());
    }


    public static enum getCellValue {
        IntegerType, DoubleType, StringType, BooleanType; 

        @SuppressWarnings("unchecked")
        public static <T> T comeback(XSSFSheet sheet, String cellAddress) {
            CellReference cellReference = new CellReference(cellAddress); 
            Row row = sheet.getRow(cellReference.getRow());
            Cell cell = row.getCell(cellReference.getCol()); 
            
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

    @SuppressWarnings("unchecked")
    public static void main(String[ ] args) { 
       
        String src_file_name;
        XSSFSheet sheet = null;
        XSSFWorkbook workbook = null;
        String[] paragraph_cols = {"E", "F", "G", "H"};
        String[][] options_paragraph_cols = {
            {"M", "N", "O", "P"},
            {"V", "W", "X", "Y"},
            {"AE", "AF", "AG", "AH"},
            {"AN", "AO", "AP", "AQ"}
        };
        String[] options_data_keys = {"optionId", "value", "nextQuestionId", "title", "url"};
        String[][] options_data_cols = {
            {"I", "J", "K", "L", "Q"},
            {"R", "S", "T", "U", "Z"},
            {"AA", "AB", "Ac", "AD", "AI"},
            {"AJ", "AK", "AL", "AM", "AR"}
        };
        


        if (args.length == 0){
            src_file_name = "../data/LAT-quiz-content.xlsx";
        }else{
            src_file_name = args[0];
        }

        System.out.println("Attempting to load "+src_file_name);

        try {
            FileInputStream file = new FileInputStream(new File(src_file_name));
            System.out.println("Loaded "+src_file_name);
            workbook = new XSSFWorkbook(file);
            sheet = workbook.getSheetAt(0);
            System.out.println("Loaded Sheet"+sheet.getSheetName());
        } catch (FileNotFoundException e) {
            System.out.println("File "+src_file_name+" was not found");
            System.exit(-1);
        } catch (IOException e) {
            System.out.println("File "+src_file_name+" was not a properly format XSLX file");
            System.exit(-1);
        }

        JSONObject json_data = new JSONObject();
        JSONArray questions = new JSONArray();


        System.out.println("Iterating though the row in  Sheet"+sheet.getSheetName());

        Iterator<Row> rowIterator = sheet.iterator();
        while (rowIterator.hasNext()){
            Row row = rowIterator.next();

            // Skipping rows 
            if (row.getRowNum() <2){continue;}
            Cell test_cell = row.getCell(1); 
            if(test_cell == null){continue;}
            if(test_cell.getCellType() == CellType.BLANK){continue;}

            JSONObject question_obj = new JSONObject();
            
            // System.out.println(" -- Row "+(row.getRowNum()+1));

            question_obj.put("questionId", getCellValue.comeback(sheet, "A"+(row.getRowNum()+1)));
            question_obj.put("type", getCellValue.comeback(sheet, "C"+(row.getRowNum()+1)));
            question_obj.put("progressBarStage", getCellValue.comeback(sheet, "D"+(row.getRowNum()+1)));
            question_obj.put("notificationType", getCellValue.comeback(sheet, "AS"+(row.getRowNum()+1)));
            question_obj.put("notificationTitle", getCellValue.comeback(sheet, "AT"+(row.getRowNum()+1)));
            question_obj.put("notificationMessge", getCellValue.comeback(sheet, "AU"+(row.getRowNum()+1)));
            question_obj.put("conditionals", getCellValue.comeback(sheet, "AV"+(row.getRowNum()+1)));

            JSONObject question_content_obj = new JSONObject();
            question_content_obj.put("title", getCellValue.comeback(sheet, "B"+(row.getRowNum()+1)));

            JSONArray paragraph_array = new JSONArray();

            for (String paragraph_col : paragraph_cols) {
                String paragraph_cell_value = getCellValueString(sheet, paragraph_col+(row.getRowNum()+1));
                if (paragraph_cell_value != ""){
                    JSONObject paragraph_content = new JSONObject();
                    paragraph_content.put("paragraphText", paragraph_cell_value);
                    paragraph_array.add(paragraph_content);
                }   
            }

            question_content_obj.put("paragraphs", paragraph_array);
            question_obj.put("content", question_content_obj);

            JSONArray options_array = new JSONArray();

            for(int option_count = 0; option_count < 4; ++option_count) {
                JSONObject option = new JSONObject();
                for(int data_count = 0; data_count < 5; ++data_count) {
                    option.put(options_data_keys[data_count], getCellValue.comeback(sheet, options_data_cols[option_count][data_count]+(row.getRowNum()+1)));
                }

                JSONArray option_paragraph_array = new JSONArray();
                for (String option_paragraph_col : options_paragraph_cols[option_count]) {
                    String option_paragraph_cell_value = getCellValue.comeback(sheet, option_paragraph_col+(row.getRowNum()+1));
                    if (option_paragraph_cell_value != ""){
                        JSONObject option_paragraph_content = new JSONObject();
                        option_paragraph_content.put("paragraphText", option_paragraph_cell_value);
                        option_paragraph_array.add(option_paragraph_content);
                    }   
                }

                option.put("paragraphs", option_paragraph_array);
                options_array.add(option);

            }

            question_obj.put("options", options_array);


            questions.add(question_obj);

            // Iterator<Cell> cellIterator = row.cellIterator();   //iterating over each column  
            // while (cellIterator.hasNext()){  
            //     Cell cell = cellIterator.next();  
            //     String val = getCellValueString(sheet, cell.getAddress().toString());
            //     System.out.println(" -- Cell "+cell.getAddress().toString()+": "+val);
            // }
            // System.out.println("");
        }
        json_data.put("questions", questions);

        // System.out.println(json_data.toJson());

        String timestamp = now();
        String out_file_name = "./quiz.json."+timestamp+"_out";

        System.out.println("Finished processing "+src_file_name);
        System.out.println("Writing JSON to  "+out_file_name);

        try {
            
            FileWriter quiz_json_file = new FileWriter(out_file_name);
            quiz_json_file.write(json_data.toJSONString());
            quiz_json_file.close();
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


