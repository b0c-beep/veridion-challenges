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
from datetime import datetime

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
    if text is None:
        return text
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
    if text is None: 
        return None
    usa_addresses = pyap.parse(text, country='US')
    uk_addresses = pyap.parse(text, country='GB')

    # Convert extracted addresses into strings for easy handling
    extracted_addresses = []

    for address in usa_addresses:
        extracted_addresses.append(str(address))

    for address in uk_addresses:
        extracted_addresses.append(str(address))

    return extracted_addresses if extracted_addresses else None

def count_domains_in_snappy(file_path):
    """Return the number of domains in a Snappy Parquet file."""
    # Read the Parquet file
    df = pd.read_parquet(file_path, engine='pyarrow') 
    
    # Return the number of rows in the 'domain' column
    return df['domain'].nunique()  # Use nunique() if domains might repeat, otherwise use len(df)

def apply_stats_colors(worksheet, stats_df, colors):
    """Apply background colors to stats rows based on the metric."""
    # Apply fill colors to rows based on the metric
    for row_num in range(len(stats_df)):

        if row_num == 0:  
            continue  # Skip the first row (header)
        elif row_num == 1:
            fill_color = colors['Reachable']
        elif row_num == 2:
            fill_color = colors['Unreachable']
        elif row_num == 3:
            fill_color = colors['No Address']
        else:
            fill_color = None


        if fill_color:
            fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            # Apply the fill to the correct row in the worksheet
            for col_num in range(1, len(stats_df.columns) + 1):
                # Adjust for where stats_df starts in the worksheet
                worksheet[f'{get_column_letter(col_num)}{len(results) + row_num + 3}'].fill = fill  # +3 for offset

    
# Save the results to an Excel file
def save_results_to_excel(results):
    """Save the results to an Excel file, adjusting column widths and applying conditional row coloring."""
    df = pd.DataFrame(results)

    output_path = './challenge_1/results.xlsx'

    total_sites = len(results)
    
    # Count reachable, unreachable, and reachable-but-no-address
    reachable_count = sum(1 for result in results if result['Status'] == 'Reachable')
    unreachable_count = sum(1 for result in results if result['Status'] == 'Unreachable')
    no_address_count = sum(1 for result in results if result['Status'] == 'Reachable - No Addresses')

    # Calculate percentages
    reachable_percentage = (reachable_count / total_sites) * 100
    unreachable_percentage = (unreachable_count / total_sites) * 100
    no_address_percentage = (no_address_count / total_sites) * 100

    # Create a DataFrame for the stats
    stats_data = {
        'Metric': ['Reachable sites', 'Unreachable sites', 'Reachable but no addresses', 'Total sites checked'],
        'Count': [reachable_count, unreachable_count, no_address_count, total_sites],
        'Percentage': [f'{reachable_percentage:.2f}%', f'{unreachable_percentage:.2f}%', f'{no_address_percentage:.2f}%', None]  # Fixed total sites percentage
    }
    stats_df = pd.DataFrame(stats_data)

    # Color for different metrics
    colors = {
        'Reachable': 'C6EFCE',  # Light Green
        'Unreachable': 'FFC7CE',  # Light Red
        'No Address': 'D9D9D9',  # Light Gray
    }

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
        
        # Write stats DataFrame starting just below the main data
        stats_df.to_excel(writer, index=False, sheet_name='Results', startrow=len(df) + 2)  # Start from the row after the results

        # Call your coloring function here
        apply_stats_colors(worksheet, stats_df, colors)
        
    #print(f"Results saved to {output_path}")

def display_stats(results):
    """Calculate and display statistics of reachable, unreachable, and reachable-but-no-address sites."""
    total_sites = len(results)
    
    # Count reachable, unreachable, and reachable-but-no-address
    reachable_count = sum(1 for result in results if result['Status'] == 'Reachable')
    unreachable_count = sum(1 for result in results if result['Status'] == 'Unreachable')
    no_address_count = sum(1 for result in results if result['Status'] == 'Reachable - No Addresses')

    # Calculate percentages
    reachable_percentage = (reachable_count / total_sites) * 100
    unreachable_percentage = (unreachable_count / total_sites) * 100
    no_address_percentage = (no_address_count / total_sites) * 100

    # Display stats with colors
    print("\n===== " + colored("Summary of Results", 'cyan') + " =====")
    print(f"Total sites checked: {colored(total_sites, 'white')}")
    print(f"Reachable sites: {colored(reachable_count, 'green')} ({colored(f'{reachable_percentage:.2f}%', 'green')})")
    print(f"Unreachable sites: {colored(unreachable_count, 'red')} ({colored(f'{unreachable_percentage:.2f}%', 'red')})")
    print(f"Reachable but no addresses: {colored(no_address_count, 'yellow')} ({colored(f'{no_address_percentage:.2f}%', 'yellow')})")
    print("==============================\n")



domains_count = count_domains_in_snappy(websites_path)
# Loop through the first 10 websites
for idx, website in enumerate(df['domain']):
    try:
        print(f"Checking website {idx + 1}/{domains_count}: {website}")
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
                'PyAP': pyap_results if pyap_results else 'N/A',
            })
            save_results_to_excel(results)
            display_stats(results)
        else:
            print(colored(f"Website {website} is not reachable. Status code: {response.status_code}", 'red'))
            results.append({
                'Domain': website,
                'URL': f'=HYPERLINK("{url}", "{url}")',
                'Status': 'Unreachable',
                'PyAP': 'N/A',
            })
            save_results_to_excel(results)
            display_stats(results)
    except requests.exceptions.RequestException as e:
        print(colored(f"Error reaching {website}: {e}", 'red'))
        results.append({
            'Domain': website,
            'URL': f'=HYPERLINK("{url}", "{url}")',
            'Status': 'Unreachable',
            'PyAP': 'N/A',
        })
        save_results_to_excel(results)
        display_stats(results)

# Save results to Excel
#save_results_to_excel(results)
