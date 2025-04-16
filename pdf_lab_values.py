import pdfplumber
import re
import pandas as pd
import sys
from collections import defaultdict
from datetime import datetime
from colorama import init, Fore, Style
import os

# Initialize Colorama for cross-platform terminal colors
init(autoreset=True)

# --- Helper Function ---
def get_vertical_center(word):
    """Calculates the vertical center of a pdfplumber word dictionary."""
    return (word['top'] + word['bottom']) / 2

# --- Main Extraction Function (Coordinate-based & Conditional Logic) ---
def extract_lab_data_coords(pdf_path):
    """
    Extracts lab result dates and values from a PDF report using word coordinates.
    Includes conditional logic for different layout tolerances (e.g., for FCP)
    and handles non-numeric results like '<0.5', '<0.6', '<=50'.
    """
    data = []

    # --- Determine Test Type from filename ---
    # Tries to get the last part of the filename before the extension
    # Assumes names like "PatientA_CRP.pdf" or just "FCP.pdf"
    try:
        base_name = os.path.basename(pdf_path)
        test_type = base_name.split('.')[0].upper().split('_')[-1]
        if "ALB" in test_type: test_type = "ALBM"
        elif "CRP" in test_type: test_type = "CRP"
        elif "FCP" in test_type: test_type = "FCP"
        else: test_type = "UNKNOWN"
    except IndexError:
        test_type = "UNKNOWN"

    # --- Configuration Parameters (ADJUST IF NEEDED FOR NEW LAYOUTS) ---
    RESULT_X_MIN, RESULT_X_MAX = 30, 100  # Horizontal range for Result column
    DATE_X_MIN = 490                    # Date components must be right of this X-coord
    MONTH_DAY_ALIGN_TOLERANCE = 5       # Max vertical distance between Month and Day words
    DATE_ABOVE_RESULT_MIN_DEFAULT = 5
    DATE_ABOVE_RESULT_MAX_DEFAULT = 25
    YEAR_ALIGN_TOLERANCE_DEFAULT = 5

    # --- Apply Default Tolerances ---
    date_above_result_min = DATE_ABOVE_RESULT_MIN_DEFAULT
    date_above_result_max = DATE_ABOVE_RESULT_MAX_DEFAULT
    year_align_tolerance = YEAR_ALIGN_TOLERANCE_DEFAULT

    # --- Adjust Tolerances Conditionally for Known Layout Variations ---
    if test_type == "FCP":
        date_above_result_min = -5
        date_above_result_max = 20
        year_align_tolerance = 15

    # --- Regex for validation ---
    month_pattern = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec),?$")
    day_pattern = re.compile(r"^\d{1,2}$")
    year_pattern = re.compile(r"^\d{4}$")
    result_pattern = re.compile(r"^(?:<0\.5|<0\.6|<=50|<100|\d+(?:\.\d+)?)$")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_words = []
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words(x_tolerance=2, y_tolerance=2)
                if words:
                    for word in words: word['page_num'] = page_num + 1
                    all_words.extend(words)
            if not all_words: return []  # Return empty if PDF has no extractable words

            # --- Categorize Words ---
            potential_results = []
            potential_months = []
            potential_days = []
            potential_years = []
            for word in all_words:
                text = word['text']
                x0 = word['x0']
                if RESULT_X_MIN <= x0 < RESULT_X_MAX and result_pattern.match(text):
                    potential_results.append(word)
                    continue
                if x0 >= DATE_X_MIN:
                    if month_pattern.match(text): potential_months.append(word)
                    elif day_pattern.match(text):
                        try:
                            if 1 <= int(text) <= 31: potential_days.append(word)
                        except ValueError: pass
                    elif year_pattern.match(text): potential_years.append(word)

            potential_results.sort(key=lambda w: (w['page_num'], w['top'], w['x0']))
            used_date_word_ids = set()

            # --- Match Results to Dates ---
            for res_word in potential_results:
                res_val_str = res_word['text']
                res_y = get_vertical_center(res_word)

                # 1. Find best aligned Year
                best_year_match = None
                min_year_dist = float('inf')
                for year_word in potential_years:
                    year_id = f"P{year_word['page_num']}-Y{year_word['top']:.0f}-X{year_word['x0']:.0f}"
                    if year_id in used_date_word_ids: continue
                    year_y = get_vertical_center(year_word)
                    y_diff = abs(res_y - year_y)
                    page_diff = abs(res_word['page_num'] - year_word['page_num'])
                    if y_diff < year_align_tolerance and page_diff <= 1:
                        dist = y_diff + (page_diff * 10)
                        if dist < min_year_dist:
                            min_year_dist = dist
                            best_year_match = year_word
                if not best_year_match: continue

                # 2. Find best Month/Day pair positioned correctly relative to Result
                best_month_day_pair = None
                min_month_day_dist = float('inf')
                for month_word in potential_months:
                    month_id = f"P{month_word['page_num']}-Y{month_word['top']:.0f}-X{month_word['x0']:.0f}"
                    if month_id in used_date_word_ids: continue
                    month_y = get_vertical_center(month_word)
                    y_diff_res = res_y - month_y
                    page_diff_month = abs(res_word['page_num'] - month_word['page_num'])
                    if date_above_result_min < y_diff_res < date_above_result_max and page_diff_month <= 1:
                        for day_word in potential_days:
                            day_id = f"P{day_word['page_num']}-Y{day_word['top']:.0f}-X{day_word['x0']:.0f}"
                            if day_id in used_date_word_ids or day_id == month_id or day_word['page_num'] != month_word['page_num']: continue
                            day_y = get_vertical_center(day_word)
                            y_diff_md = abs(month_y - day_y)
                            if y_diff_md < MONTH_DAY_ALIGN_TOLERANCE:
                                dist = y_diff_res + y_diff_md + (page_diff_month * 10)
                                if dist < min_month_day_dist:
                                    min_month_day_dist = dist
                                    best_month_day_pair = (month_word, day_word)

                # 3. If full set found, format and store
                if best_month_day_pair:
                    found_month, found_day = best_month_day_pair
                    found_year = best_year_match
                    month_str = found_month['text'].replace(',', '')
                    day_str = found_day['text']
                    year_str = found_year['text']
                    formatted_date = f"{month_str} {day_str} {year_str}"

                    # Handle non-numeric and numeric values
                    try:
                        val = None
                        if res_val_str == "<0.5": val = 0.5
                        elif res_val_str == "<0.6": val = 0.6
                        elif res_val_str == "<=50": val = 50
                        elif res_val_str == "<100": val = 100
                        else:
                            val = float(res_val_str)
                            if val.is_integer(): val = int(val)

                        if val is not None:
                            data.append({"Date": formatted_date, "Value": val, "Test": test_type})
                            used_date_word_ids.add(f"P{found_year['page_num']}-Y{found_year['top']:.0f}-X{found_year['x0']:.0f}")
                            used_date_word_ids.add(f"P{found_month['page_num']}-Y{found_month['top']:.0f}-X{found_month['x0']:.0f}")
                            used_date_word_ids.add(f"P{found_day['page_num']}-Y{found_day['top']:.0f}-X{found_day['x0']:.0f}")
                    except ValueError:
                        print(f"{Fore.RED}Warning: Could not convert result '{res_val_str}' to number for date {formatted_date} in {pdf_path}{Style.RESET_ALL}")

    except FileNotFoundError:
        print(f"{Fore.RED}Error: File not found at {pdf_path}{Style.RESET_ALL}")
        return []  # Return empty list on file error
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred while processing {pdf_path}: {e}{Style.RESET_ALL}")
        return []  # Return empty list on other errors
    return data


# --- Main Execution Block ---
if __name__ == "__main__":

    # --- 1. Get PDF File Paths from Command Line ---
    if len(sys.argv) < 2:
        # sys.argv[0] is the script name itself
        print(f"{Fore.RED}Usage Error:{Style.RESET_ALL}")
        print(f"  python {os.path.basename(sys.argv[0])} <pdf_file_1> [<pdf_file_2> ...]")
        print("\nExample:")
        print(f"  python {os.path.basename(sys.argv[0])} PatientA_CRP.pdf PatientA_ALBM.pdf")
        sys.exit("Please provide at least one PDF file path as an argument.")

    # Use all arguments after the script name as file paths
    files_to_process = sys.argv[1:]
    print(f"Attempting to process files: {', '.join(files_to_process)}")

    # Define colors for test types (add more as needed)
    test_colors = {
        'ALBM': Fore.BLUE,
        'CRP': Fore.MAGENTA,
        'FCP': Fore.YELLOW,
        'DEFAULT': Fore.WHITE,  # Default for unknown types
        'UNKNOWN': Fore.RED    # For types that couldn't be identified
    }

    # --- 2. Get Index Date from User ---
    index_date = None
    while index_date is None:
        date_str = input(f"Enter Index Date ({Fore.YELLOW}DD/MMM/YYYY{Style.RESET_ALL} format, e.g., 15/Apr/2024): ")
        try:
            try: index_date = datetime.strptime(date_str, "%d/%b/%Y")
            except ValueError: index_date = datetime.strptime(date_str, "%d/%B/%Y")
            print(f"Index Date set to: {Fore.CYAN}{index_date.strftime('%d/%b/%Y')}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid date format. Please use DD/MMM/YYYY (e.g., 01/Jan/2023 or 15/Apr/2024).{Style.RESET_ALL}")

    # --- 3. Process Each File and Combine Results ---
    all_results = []
    test_types_found = set()
    for filename in files_to_process:
        print(f"\nProcessing {filename}...")
        extracted_data = extract_lab_data_coords(filename)

        if not extracted_data:
            print(f"{Fore.YELLOW}No data extracted from {filename}.{Style.RESET_ALL}")
            continue

        for record in extracted_data:
            test_types_found.add(record['Test'])
            try:
                record['ParsedDate'] = pd.to_datetime(record['Date'], format='%b %d %Y', errors='coerce').to_pydatetime()
                if pd.isna(record['ParsedDate']):
                    print(f"{Fore.RED}Warning: Could not parse date '{record['Date']}' from {filename}. Record skipped.{Style.RESET_ALL}")
                    continue
                all_results.append(record)
            except Exception as e:
                print(f"{Fore.RED}Warning: Error processing date '{record.get('Date', 'N/A')}' from {filename}: {e}{Style.RESET_ALL}")

    if not all_results:
        print(f"{Fore.RED}\nNo valid data could be extracted and parsed from any files.{Style.RESET_ALL}")
        sys.exit("Exiting: No data to display.")

    # --- 4. Sort All Results Chronologically ---
    all_results.sort(key=lambda x: x['ParsedDate'], reverse=True)

    # --- 5. Categorize Results ---
    most_recent_pre_index_by_test = {}
    post_index_results = []
    processed_pre_index_tests = set()

    for record in all_results:
        test_type = record['Test']
        if record['ParsedDate'] < index_date:
            if test_type not in processed_pre_index_tests and test_type != "UNKNOWN":
                most_recent_pre_index_by_test[test_type] = record
                processed_pre_index_tests.add(test_type)
        else:
            post_index_results.append(record)

    grouped_post_index = defaultdict(list)
    post_index_results.sort(key=lambda x: x['ParsedDate'])
    for record in post_index_results:
        date_str = record['ParsedDate'].strftime('%d/%b/%Y')
        grouped_post_index[date_str].append({"Test": record['Test'], "Value": record['Value']})

    # --- 6. Print Formatted Results ---
    print(f"\n{Style.BRIGHT}--- Results Relative to Index Date: {index_date.strftime('%d/%b/%Y')} ---{Style.RESET_ALL}")

    print(f"\n{Style.BRIGHT}Most Recent PRE-INDEX Results (per test type):{Style.RESET_ALL}")
    pre_index_found = False
    if most_recent_pre_index_by_test:
        for test_type in sorted(most_recent_pre_index_by_test.keys()):
            record = most_recent_pre_index_by_test[test_type]
            color = test_colors.get(test_type, test_colors['DEFAULT'])
            date_display = record['ParsedDate'].strftime('%d/%b/%Y') if 'ParsedDate' in record and record['ParsedDate'] else "Date Error"
            value_display = record.get('Value', 'N/A')
            if isinstance(value_display, float) and not value_display.is_integer(): value_display = f"{value_display:.1f}"
            elif isinstance(value_display, float): value_display = int(value_display)

            print(f"  - {color}{test_type}{Style.RESET_ALL} ({date_display}): {value_display}")
            pre_index_found = True
    if not pre_index_found:
        print(f"  {Fore.YELLOW}(No results found before the index date for any specified test type){Style.RESET_ALL}")

    # Display Post-Index Results
    print(f"\n{Fore.CYAN}{Style.BRIGHT}POST-INDEX Results (including index date):{Style.RESET_ALL}")
    if grouped_post_index:
        for date_str in sorted(grouped_post_index.keys(), key=lambda d: datetime.strptime(d, '%d/%b/%Y')):
            results = grouped_post_index[date_str]
            print(f"  {Fore.CYAN}{date_str}{Style.RESET_ALL}")
            results.sort(key=lambda r: r['Test'])
            for res in results:
                color = test_colors.get(res['Test'], test_colors['DEFAULT'])
                value_display = res.get('Value', 'N/A')
                if isinstance(value_display, float) and not value_display.is_integer(): value_display = f"{value_display:.1f}"
                elif isinstance(value_display, float): value_display = int(value_display)

                print(f"    - {color}{res['Test']}{Style.RESET_ALL}: {value_display}")
    else:
        print(f"  {Fore.CYAN}(No results found on or after the index date){Style.RESET_ALL}")
