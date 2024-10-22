import pandas as pd
from bs4 import BeautifulSoup
import requests

def read_snappy_file_to_dataframe(snappy_file_path):
    """Reads and decompresses the Snappy file and returns the contents as a DataFrame."""
    with open(snappy_file_path, 'rb') as f:
        compressed_data = f.read()

    # Decompress the snappy file content
    decompressed_data = snappy.decompress(compressed_data)

    # Load the decompressed data into a pandas DataFrame (assuming CSV format in the Snappy file)
    df = pd.read_csv(pd.compat.StringIO(decompressed_data.decode('utf-8')))  # If it's CSV content
    return df

def check_site_for_domain(site_url, domain_to_check):
    """Checks if the site contains the specified domain."""
    try:
        # Make a request to the site
        response = requests.get(site_url)
        response.raise_for_status()  # Raise an error if the request failed

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check if the domain appears anywhere in the page
        if domain_to_check in soup.prettify():
            print(f"Domain '{domain_to_check}' found on the site: {site_url}")
        else:
            print(f"Domain '{domain_to_check}' NOT found on the site: {site_url}")

    except requests.RequestException as e:
        print(f"Error checking the site {site_url}: {e}")

# Usage example
snappy_file_path = './data.snappy'  # Replace with your snappy file path
domain_to_check = 'example.com'     # Replace with the domain you want to check

# Read the decompressed data from the Snappy file into a DataFrame
df = read_snappy_file_to_dataframe(snappy_file_path)

# Assuming your DataFrame contains a column named 'Site URL'
for index, row in df.iterrows():
    site_url = row['Site URL']  # Replace 'Site URL' with the actual column name in your data
    print(f"Checking site: {site_url}")
    check_site_for_domain(site_url, domain_to_check)
