# Python PDF Lab Value Parser

## Overview
This Python script automates the extraction of lab result values and their corresponding collection dates from text-based PDF lab reports. It is designed to process reports for common tests like **Albumin (ALBM)**, **C-Reactive Protein (CRP)**, and **Fecal Calprotectin (FCP)**, among others if the layout is similar.

The primary goal is to increase efficiency for researchers or clinicians needing to transcribe longitudinal lab data into Electronic Data Capture (EDC) systems or spreadsheets for studies. It achieves this by:

- Parsing multiple PDF reports for a single subject.
- Prompting the user for a study-specific "Index Date".
- Categorizing extracted results relative to the index date.
- Displaying the results clearly in the terminal, grouped by date, with color-coding for different test types.
- Specifically highlighting the most recent pre-index result for each test type and listing all post-index results chronologically.

## How it Works

### 1. **PDF Parsing with `pdfplumber`**
The script uses the `pdfplumber` library to open text-based PDFs and extract individual words along with their precise coordinates (`x0`, `y0`, `top`, `bottom`) on each page. This allows the script to identify the location of **result values** and **date components** (Month, Day, Year) within the report. `pdfplumber` is particularly useful for extracting structured data from PDFs with consistent layouts, such as lab reports.

### 2. **Coordinate-Based Matching**
The script identifies potential **Result** values and **Date** components based on their expected **horizontal** positions within the page layout. The coordinates of the text are parsed and matched to specific columns for results and dates:

- **Results** are usually located in the left column (`x0` between 30 and 100).
- **Dates** are typically found on the right column (`x0` greater than 490).

The `x_tolerance` and `y_tolerance` parameters are adjusted to capture words accurately even when the layout slightly varies.

### 3. **Spatial Relationship Logic**
Once potential results and dates are identified, the script uses the **vertical proximity** of the words to match a result value with its corresponding date. For example, the script expects the **Month/Day** to be slightly above the **Result/Year**.

The script includes **conditional logic** to adjust the vertical tolerances when specific layout variations are known (such as those seen in some FCP reports).

### 4. **Using Regular Expressions (Regex)**
Regex is used to validate and match **non-numeric results** (e.g., `<0.5`, `<0.6`, `<=50`) and standard numeric values. The script uses the following patterns:

- **Month**: Matches standard month abbreviations (e.g., Jan, Feb, Mar).
- **Day**: Matches numeric day values (1–31).
- **Year**: Matches four-digit years (e.g., 2024).
- **Result**: Matches numeric results or specific non-numeric values, such as `<0.5`, `<0.6`, and `<=50`.

Here’s an example of the regex used to handle result values:

```python
result_pattern = re.compile(
    r"^(?:<0\.5|<0\.6|<=50|<100|\d+(?:\.\d+)?)$"
)
```

This pattern matches:

Non-numeric results like <0.5, <0.6, <=50.

Standard numeric values (integers or floating-point).

5. Date Parsing and Categorization
Once the results and dates are matched, the script parses the extracted date strings into datetime objects using pandas and compares them to the user-provided Index Date. The results are categorized into:

Most recent pre-index result for each test.

All post-index results grouped by date.

6. Terminal Output with Color-Coding
The results are displayed in the terminal with color-coding, using the colorama library:

ALBM results are displayed in blue.

CRP results are displayed in magenta.

FCP results are displayed in yellow.

Other test results are displayed in the default color.

This helps differentiate the test types and makes the output easier to scan.

Requirements
Python 3.x

Libraries:

pdfplumber: For extracting text and coordinates from PDFs.

pandas: For handling dates and structured data.

colorama: For color-coded terminal output.

You can install the required libraries using pip:

bash
Copy
Edit
pip install pdfplumber pandas colorama
Usage
To run the script, pass the file paths of the PDF reports as command-line arguments. For example:

bash
Copy
Edit
python labs_extractor.py PatientA_CRP.pdf PatientA_ALBM.pdf PatientA_FCP.pdf
The script will:

Ask for an Index Date in DD/MMM/YYYY format (e.g., 15/Apr/2024).

Extract the lab values and dates from the PDFs.

Categorize and display results relative to the index date:

Most recent pre-index result for each test.

All post-index results, grouped by date.

Example Output
Here’s the actual terminal output showing how the script works:

![Terminal Output](https://raw.githubusercontent.com/PedTavv/Python-PDF-Lab-Value-Parser/master/assets/terminal_output.png)
