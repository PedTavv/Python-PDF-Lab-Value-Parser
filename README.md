# Python PDF Lab Value Parser

## Overview
This Python script automates the extraction of lab result values and their collection dates from text-based PDF lab reports. It is designed for common tests such as **Albumin (ALBM)**, **C-Reactive Protein (CRP)**, and **Fecal Calprotectin (FCP)**. The goal is to streamline data transcription into Electronic Data Capture (EDC) systems—saving time and improving accuracy. By offering color-coded output in the terminal, it increases data input efficiency and reduces errors.

The script prompts the user for a study-specific **Index Date** (e.g., treatment initiation) and categorizes all lab results as pre-index or post-index, facilitating quick and structured analysis across timepoints.

---

## Key Features

- **Text-Based PDF Parsing**: Utilizes `pdfplumber` to extract structured data with precise coordinates, enabling accurate parsing even in multi-column layouts.
- **Coordinate-Aware Matching**: Matches lab results to corresponding dates based on horizontal and vertical proximity (x/y position logic).
- **Robust Regex Logic**: Captures both numeric and non-numeric result values (e.g., `51`, `<0.5`, `<=50`) using flexible regular expressions.
- **Index Date Categorization**: Prompts for a user-defined **Index Date** and:
  - Highlights the most recent **pre-index** result for each test.
  - Lists all **post-index** results, organized by collection date.
- **Color-Coded Output**: Increases readability and allows easy differentiation of test types:
  - **Blue** → ALBM
  - **Magenta** → CRP
  - **Yellow** → FCP

---

## How It Works

### 1. **PDF Parsing with `pdfplumber`**
The script extracts every word along with its `(x, y)` coordinates from each page. This allows precise identification of relevant data, even in complex multi-column reports.

### 2. **Spatial Matching**
- **Result Values**: Typically found in the left column of the report.
- **Date Components (Month, Day, Year)**: Extracted from the right column.
- The script uses vertical alignment to associate each result with the correct date, ensuring accuracy even if the layout varies.

### 3. **Date-Based Categorization**
- The user is prompted to enter an **Index Date** (e.g., `15/Apr/2024`).
- The script:
  - **Identifies the most recent pre-index** result for each test.
  - **Groups all post-index results** chronologically for easy analysis.

### 4. **Terminal Output**
The results are printed with color coding based on the test type, improving clarity and making it easier to differentiate between test categories.

---

## Conclusion
This script showcases how Python can be used in clinical data workflows to automate repetitive tasks, reduce manual errors, and save time in medical research, particularly for longitudinal chart reviews and lab data processing.


Example Output
Here’s the actual terminal output showing how the script works:

![Terminal Output](https://raw.githubusercontent.com/PedTavv/Python-PDF-Lab-Value-Parser/master/assets/terminal_output.png)
