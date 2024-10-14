import pandas as pd
import requests
from bs4 import BeautifulSoup
from termcolor import colored
from colorama import init

init()  # Initialize colorama   

websites_path = './challenge_1/list_of_company_websites.snappy.parquet'

# Set display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Read the Parquet file
df = pd.read_parquet(websites_path, engine='pyarrow') 

# Display the first few rows of the dataframe
#print(df.head())

# Loop through the first 10 websites
for idx, website in enumerate(df['domain']):
    try:
        print(f"Checking website {idx + 1}: {website}")
        url = 'http://' + website  
        # Send a GET request to the website
        response = requests.get(url, timeout=5)  # timeout after 5 seconds
        if response.status_code == 200:
            # Print reachable websites in green
            print(colored(f"Website {website} is reachable.", 'green'))
        else:
            # Print unreachable websites in red
            print(colored(f"Website {website} is not reachable. Status code: {response.status_code}", 'red'))
    except requests.exceptions.RequestException as e:
        # Print unreachable websites with error details in red
        print(colored(f"Error reaching {website}: {e}", 'red'))
