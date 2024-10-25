import pandas as pd
from bs4 import BeautifulSoup
import requests
import pyap
from urllib.parse import urljoin, urlparse
from cleantext import clean
from requests.exceptions import RequestException, SSLError

def read_parquet_file(parquet_file_path):
    """Reads the Snappy-compressed Parquet file and returns the contents as a DataFrame."""
    try:
        # Reading the Parquet file
        df = pd.read_parquet(parquet_file_path)
        return df
    except Exception as e:
        print(f"Error reading Parquet file: {e}")
        return None

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

def scrape_page_content(url):
    """Fetches and cleans the page content."""
    try:
        response = requests.get(url, verify=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text (adjust this as per the structure of the page)
        #page_content = soup.get_text(separator='\n').strip()
        
        # Return the content, clean it further if needed
        return soup
    except SSLError:
        # Skip if SSL certificate is invalid
        print(f"Skipping insecure site (SSL verification failed): {url}")
    except RequestException as e:
        # Catch any other request-related errors
        print(f"Error fetching {url}: {e}")
    return None

def scrape_links_and_content(start_url):
    """Scrapes all reachable pages starting from the given URL and visits unique links only."""
    
    visited_urls = set()  # Set to keep track of visited URLs
    visited_hrefs = set()  # Set to keep track of visited hrefs
    #urls_to_visit = [start_url]  # List to manage URLs to visit
    all_scraped_content = ""  # String to hold all scraped content

    page_soup = scrape_page_content(start_url)
    if page_soup is None:
        print(f"Failed to scrape the content of {start_url}")
        return None
    all_scraped_content += page_soup.get_text() + '\n'  # Append the content to the main string

    # Find all <a> tags on the page
    links = page_soup.find_all('a', href=True)  # Only get links that have an href attribute

    for link in links:
        href = link['href']
        full_url = urljoin(start_url, href)  # Construct absolute URL

        # Check if the href is internal and has not been visited
        if urlparse(full_url).netloc == urlparse(start_url).netloc and href not in visited_hrefs:
            visited_urls.add(full_url)  # Mark the URL as visited
            visited_hrefs.add(href)  # Mark the href as visited
            link_soup = scrape_page_content(full_url)  # Scrape the content of the link
            all_scraped_content += link_soup.get_text() + '\n'  # Append the content to the main string

    return all_scraped_content

def extract_pyap(text):
    """Extract both US and UK addresses using pyap and ensure uniqueness."""
    # Return None if the input text is None
    if text is None: 
        return None
    
    # Use a set to store unique addresses
    unique_addresses = set()

    # Extract US addresses
    usa_addresses = pyap.parse(text, country='US')
    for address in usa_addresses:
        unique_addresses.add(str(address))  # Add to set for uniqueness

    # Extract UK addresses
    uk_addresses = pyap.parse(text, country='GB')
    for address in uk_addresses:
        unique_addresses.add(str(address))  # Add to set for uniqueness

    # Return a list of unique addresses or None if no addresses found
    return list(unique_addresses) if unique_addresses else None

def save_content_to_notepad(content, file_path):
    """Save the content to a text file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Content saved to: {file_path}")
    except Exception as e:
        print(f"An error occurred while saving the content: {e}")

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

def clean_website_content2(text):
    """Clean website content by removing extra spaces, blank lines, and normalizing text."""
    if text is None:
        return text

    # Split the text into lines
    lines = text.splitlines()

    # Remove blank lines and strip extra spaces from each line
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    # Join the cleaned lines back, maintaining new lines between content
    cleaned_text = '\n'.join(cleaned_lines)

    # Optionally remove non-alphanumeric characters, keeping basic punctuation
    cleaned_text = ''.join(c for c in cleaned_text if c.isalnum() or c.isspace() or c in ";:!?")

    return cleaned_text

def main():
    # File path to the Parquet file
    parquet_file_path = './challenge_1/list_of_company_websites.snappy.parquet'  # Replace with your snappy-compressed parquet file path

    # Domain to check in each website
    domain_to_check = 'clubk-9.com'  
    url_to_check = 'https://' + domain_to_check

    # Read the Parquet data into a DataFrame
    df = read_parquet_file(parquet_file_path)
    
    website_content = scrape_links_and_content(url_to_check)
    cleaned_content = clean_website_content2(website_content)
    #cleaned_content = remove_repeating_words(cleaned_content)
    #print(website_content)
    save_content_to_notepad(cleaned_content, './challenge_1/' + domain_to_check + '.txt')
    extracted_addresses = extract_pyap(cleaned_content)
    print(extracted_addresses)

if __name__ == "__main__":
    main()
