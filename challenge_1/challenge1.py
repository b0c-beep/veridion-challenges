import pandas as pd
import requests
from bs4 import BeautifulSoup
from termcolor import colored
from colorama import init
import usaddress
import pyap
from address_parser import Parser
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Alignment
import os
from cleantext import clean

# Initialize colorama
init()  

websites_path = './challenge_1/list_of_company_websites.snappy.parquet'

# Set display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Read the Parquet file
df = pd.read_parquet(websites_path, engine='pyarrow') 

def extract_website_content(url):
    """Fetch and return the text content of the website."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text()
        else:
            print(f"Failed to retrieve {url}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching {url}: {e}")
        return None

def clean_website_content(text):
    """Clean website content by removing extra spaces and normalizing text."""
    # Remove extra whitespace
    cleaned_text = ' '.join(text.split())
    
    # Optionally remove non-alphanumeric characters, keeping basic punctuation
    cleaned_text = ''.join(c for c in cleaned_text if c.isalnum() or c.isspace() or c in ",.;:!?")
    
    # Further text normalization (you can add more rules here)
    
    return cleaned_text

# Initialize results list
results = []

def extract_pyap(text):
    """Extract both US and UK addresses using pyap."""
    # Regular expressions for detecting both US and UK addresses
    usa_addresses = pyap.parse(text, country='US')
    uk_addresses = pyap.parse(text, country='GB')

    # Convert extracted addresses into strings for easy handling
    extracted_addresses = []

    for address in usa_addresses:
        extracted_addresses.append(str(address))

    for address in uk_addresses:
        extracted_addresses.append(str(address))

    return extracted_addresses if extracted_addresses else None

# Loop through the first 10 websites
for idx, website in enumerate(df['domain'].head(10)):
    try:
        print(f"Checking website {idx + 1}: {website}")
        url = 'http://' + website
        response = requests.get(url, timeout=5)  # timeout after 5 seconds
        
        if response.status_code == 200:
            print(colored(f"Website {website} is reachable.", 'green'))
            website_content = extract_website_content(url)
            
            # Clean the website content
            cleaned_content = clean_website_content(website_content)
            
            # Extract addresses using various methods
            pyap_results = extract_pyap(cleaned_content)

            # Store the results
            results.append({
                'Domain': website,
                'URL': f'=HYPERLINK("{url}", "{url}")',
                'Status': 'Reachable' if pyap_results else 'Reachable - No Addresses',
                'Uncleaned Text': website_content,
                'Cleaned Text': cleaned_content,
                'PyAP': pyap_results if pyap_results else 'N/A',
            })
        else:
            print(colored(f"Website {website} is not reachable. Status code: {response.status_code}", 'red'))
            results.append({
                'Domain': website,
                'URL': f'=HYPERLINK("{url}", "{url}")',
                'Status': 'Unreachable',
                'Uncleaned Text': 'N/A',
                'Cleaned Text': 'N/A',
                'PyAP': 'N/A',
            })
    except requests.exceptions.RequestException as e:
        print(colored(f"Error reaching {website}: {e}", 'red'))
        results.append({
            'Domain': website,
            'URL': f'=HYPERLINK("{url}", "{url}")',
            'Status': 'Unreachable',
            'Uncleaned Text': 'N/A',
            'Cleaned Text': 'N/A',
            'PyAP': 'N/A',
        })

# Save the results to an Excel file
def save_results_to_excel(results):
    """Save the results to an Excel file, adjusting column widths and applying conditional row coloring."""
    df = pd.DataFrame(results)

    output_path = './challenge_1/results.xlsx'

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')

        workbook = writer.book
        worksheet = writer.sheets['Results']

        max_width = 50  # Set max width for columns

        # Adjust column widths
        for col_num, col_name in enumerate(df.columns, start=1):
            max_length = max(df[col_name].astype(str).map(len).max(), len(col_name))
            adjusted_width = min(max_length + 2, max_width)
            worksheet.column_dimensions[get_column_letter(col_num)].width = adjusted_width

            # Ensure text is not wrapped in each cell
            for row_num in range(1, len(df) + 2):  # +2 to account for header
                cell = worksheet.cell(row=row_num, column=col_num)
                cell.alignment = Alignment(wrap_text=False)  # Disable text wrapping

        # Apply conditional coloring to rows based on 'Status'
        for row_num in range(2, len(df) + 2):  # Data starts from row 2 (index 0 in DataFrame)
            status_cell = worksheet[f'C{row_num}']  # Column C holds the 'Status'
            status_value = status_cell.value  # Get the status value from the cell
            
            # Determine the fill color based on the 'Status'
            if status_value == 'Reachable':
                fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Green
            elif status_value == 'Reachable - No Addresses':
                fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")  # Gray (Reachable but no address)
            else:
                fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Red (Unreachable)

            # Apply the fill to the entire row
            for col_num in range(1, len(df.columns) + 1):
                worksheet[f'{get_column_letter(col_num)}{row_num}'].fill = fill

    print(f"Results saved to {output_path}")

# Save results to Excel
save_results_to_excel(results)
