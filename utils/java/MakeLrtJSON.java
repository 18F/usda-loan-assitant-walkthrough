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

This script converts the LRT spreadsheet into a JSON file readable by 
the Loan Assistance tool website. 

To Build: In the script folder run: javac MakeLrtJSON.java -cp "./lib/*"
To Run: java -cp "./lib/*:."  MakeLrtJSON [XLSX File Name: ../data/LAT-content_Mod1_2.xlsx]

The Script will recognize one positional command line argument for the
path of the XLSX file for the quiz content.  Without any input the 
script will assume the path ../data/LAT-content_Mod1_2.xlsx by default.

*/

public class MakeLrtJSON {

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
            // Get call value in source type from Sheet and Cell address 
            CellReference cellReference = new CellReference(cellAddress); 
            Row row = sheet.getRow(cellReference.getRow());
            Cell cell = row.getCell(cellReference.getCol()); 
            
            switch (cell.getCellType()){
                case STRING:
                    return (T) String.valueOf(cell.getStringCellValue().trim());
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

        @SuppressWarnings("unchecked")
        public static <T> T comeback(Cell cell) {
            // Get call value  in source type from Cell object 
            
            switch (cell.getCellType()){
                case STRING:
                    return (T) String.valueOf(cell.getStringCellValue().trim());
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
        // Get Cell value as string from Sheet and Cell address 
        CellReference cellReference = new CellReference(cellAddress); 
        Row row = sheet.getRow(cellReference.getRow());
        Cell cell = row.getCell(cellReference.getCol()); 

        switch (cell.getCellType()){
            case STRING:
                return cell.getStringCellValue().trim();
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

    public static String getCellValueString(Cell cell) { 
        // Get Cell value as string from Cell object 

        switch (cell.getCellType()){
            case STRING:
                return cell.getStringCellValue().trim();
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

        if (args.length == 0){
            src_file_name = "../data//LAT-content_Mod1_2.xlsx";
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
        JSONArray steps = new JSONArray();

        Row header_row = sheet.getRow(1);


        System.out.println("Iterating though the row in  Sheet"+sheet.getSheetName());

        Iterator<Row> rowIterator = sheet.iterator();
        while (rowIterator.hasNext()){
            Row row = rowIterator.next();

            // The Iterator seems to index the lines, not number them so we will use 
            // the real row num as row.getRowNum()  + 1

            int row_num = row.getRowNum() +1;

            // Skipping header rows
            if (row_num <3){continue;}
            // Skipping empty rows based no the ID column
            Cell test_cell = row.getCell(1); 
            if(test_cell == null){continue;}
            if(test_cell.getCellType() == CellType.BLANK){continue;}

            JSONObject step = new JSONObject();
            JSONObject content = new JSONObject();
            JSONArray paragraphs = new JSONArray();
            JSONObject bullet_paragraph = new JSONObject();
            JSONArray bullets = new JSONArray();
            JSONArray buttons = new JSONArray();



            step.put("id", getCellValue.comeback(sheet, "B"+row_num));
            step.put("title", getCellValue.comeback(sheet, "C"+row_num));
            step.put("sectionHeader", getCellValue.comeback(sheet, "E"+row_num));
            step.put("subtitle", getCellValue.comeback(sheet, "D"+row_num));
            step.put("type", getCellValue.comeback(sheet, "F"+row_num));
            step.put("progressBarStage", getCellValue.comeback(sheet, "A"+row_num));

            Iterator<Cell> cellIterator = row.iterator();
            while (cellIterator.hasNext()){
                Cell cell = cellIterator.next();
                
                // Skip Empty cells 
                // if(cell == null){continue;}
                // if(cell.getCellType() == CellType.BLANK){continue;}

                // Skip cell captured positionally above
                if (cell.getColumnIndex() < 6){continue;}


                String header = getCellValueString(header_row.getCell(cell.getColumnIndex()));
                String cell_string = getCellValueString(cell);
                
                System.out.println("Row " +row_num+": |"+header+"| - Cell "+cell.getColumnIndex()+": "+getCellValueString(cell));

                switch (header){
                    case "paragraphContent":
                        if (cell_string != ""){
                            JSONObject paragraph_content = new JSONObject();
                            paragraph_content.put("paragraphContent", cell_string);
                            paragraphs.add(paragraph_content);
                        }
                        continue;
                    
                    case "bulletContent":
                        if (cell_string != ""){
                            JSONObject bullet_content = new JSONObject();
                            bullet_content.put("bulletContent", cell_string);
                            bullets.add(bullet_content);
                        }
                        continue;
                    
                    case "type":
                        if (cell_string != ""){
                            bullet_paragraph.put("type", cell_string);
                        }
                        continue;

                    case "src":
                        if (cell_string != ""){
                            content.put("src", cell_string);
                        }
                        continue;
                    
                    case "captionText":
                        if (cell_string != ""){
                            content.put("captionText", cell_string);
                        }
                        continue;
                    
                    case "resetToStepId":
                        if (cell_string != ""){
                            step.put("resetToStepId", cell_string);
                        }
                        continue;

                    case "resetText":
                        if (cell_string != ""){
                            step.put("resetText", cell_string);
                        }
                        continue;
                    
                    case "nextStepId":
                        // A button is represented by a consecutive 5 cell blocks starting with nextStepId
                        Cell nextStepId_cell = cell;
                        Cell buttonText_cell = cellIterator.next();
                        Cell color_cell = cellIterator.next();
                        Cell textColor_cell = cellIterator.next();
                        Cell url_cell = cellIterator.next();

                        JSONObject button = new JSONObject();

                        if (getCellValueString(nextStepId_cell) == "" && getCellValueString(url_cell) == ""){
                            continue;
                        }

                        // works because null and BLANK cell are translated to "" 
                        if (getCellValueString(nextStepId_cell) == ""){
                            button.put("url", getCellValue.comeback(url_cell));
                        }else{
                            button.put("nextStepId", getCellValue.comeback(nextStepId_cell));
                        }

                        button.put("buttonText", getCellValue.comeback(buttonText_cell));
                        button.put("color", getCellValue.comeback(color_cell));
                        button.put("textColor", getCellValue.comeback(textColor_cell));



                        System.out.println(button.toJSONString());
                        buttons.add(button);
                        continue;

                    case "":
                        // Skip cells without headers, this works because getCellValueString
                        // returns "" for  null, BLANK or empty cells
                        continue;
                        
                    default:
                        // Unexpected headers are ignored
                        continue;
                        
                }
                
            }

            // Contract and store the bullet paragraph 
            if (bullets.size() > 0){
                bullet_paragraph.put("bullets", bullets);

                JSONObject bullet_paragraph_content = new JSONObject();
                bullet_paragraph_content.put("paragraphContent", bullet_paragraph);
                paragraphs.add(bullet_paragraph_content);

            }

            content.put("paragraphs", paragraphs);
            step.put("buttons", buttons);
            step.put("content", content);
            steps.add(step);


        }
        json_data.put("steps", steps);

        // System.out.println(json_data.toJson());

        String timestamp = now();
        String out_file_name = "./wizard-content.json."+timestamp+"_out";

        System.out.println("Finished processing "+src_file_name);
        System.out.println("Writing JSON to  "+out_file_name);

        try {
            
            FileWriter lrt_json_file = new FileWriter(out_file_name);
            lrt_json_file.write(json_data.toJSONString());
            lrt_json_file.close();
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


