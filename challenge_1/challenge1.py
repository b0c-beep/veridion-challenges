import pandas as pd
import requests
from bs4 import BeautifulSoup
from termcolor import colored
from colorama import init
import re

init()  # Initialize colorama   

websites_path = './challenge_1/list_of_company_websites.snappy.parquet'

# Set display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Read the Parquet file
df = pd.read_parquet(websites_path, engine='pyarrow') 

def extract_website_content(url):
    try:
        # Send an HTTP request to fetch the page content
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract all text from the page
            return soup.get_text()
        else:
            print(f"Failed to retrieve {url}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching {url}: {e}")
        return None
    

# Define a regex pattern for addresses (example: UK/US format)
address_pattern = re.compile(r'\b(?:[A-Za-z0-9.\-]+)\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Square|Sq)\b', re.IGNORECASE)
postcode_pattern = re.compile(r'\b[A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s?\d[A-Za-z]{2}\b|\d{5}(?:-\d{4})?\b')  # UK and US postcodes

def extract_address_like_content(text):
    addresses = address_pattern.findall(text)
    postcodes = postcode_pattern.findall(text)
    return addresses, postcodes


# Loop through the first 10 websites
for idx, website in enumerate(df['domain'].head(5)):
    try:
        print(f"Checking website {idx + 1}: {website}")
        url = 'http://' + website  
        # Send a GET request to the website
        response = requests.get(url, timeout=5)  # timeout after 5 seconds
        if response.status_code == 200:
            # Print reachable websites in green
            print(colored(f"Website {website} is reachable.", 'green'))
            website_content = extract_website_content(url)
            addresses, postcodes = extract_address_like_content(website_content)
            print("Addresses found:", addresses)
            print("Postcodes found:", postcodes)
        else:
            # Print unreachable websites in red
            print(colored(f"Website {website} is not reachable. Status code: {response.status_code}", 'red'))
    except requests.exceptions.RequestException as e:
        # Print unreachable websites with error details in red
        print(colored(f"Error reaching {website}: {e}", 'red'))
