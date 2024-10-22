import pandas as pd
from bs4 import BeautifulSoup
import requests
import pyap
from urllib.parse import urljoin, urlparse
from cleantext import clean

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
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract text (adjust this as per the structure of the page)
    page_content = soup.get_text(separator='\n').strip()
    
    # Return the content, clean it further if needed
    return page_content

def scrape_links_and_content(start_url):
    """Scrapes all reachable pages starting from the given URL, extracting text from address-related tags only, ensuring no duplicates."""
    
    visited_urls = set()  # Set to keep track of visited URLs
    urls_to_visit = [start_url]  # List to manage URLs to visit
    all_scraped_content = set()  # Use a set to hold unique scraped content

    while urls_to_visit:
        current_url = urls_to_visit.pop(0)  # Get the next URL to visit
        
        # Skip if we've already visited this URL
        if current_url in visited_urls:
            continue
        
        visited_urls.add(current_url)  # Mark this URL as visited
        
        try:
            # Fetch the page content
            response = requests.get(current_url)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse the page content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find and store unique text from address-related tags
            address_tags = soup.find_all(['address', 'div', 'span', 'p', 'li'])
            for tag in address_tags:
                address = tag.get_text(strip=True)
                if address:  # Ensure the tag is not empty
                    all_scraped_content.add(address)  # Add address to the set to ensure uniqueness

            # Find all <a> tags on the page
            links = soup.find_all('a', href=True)  # Only get links that have an href attribute

            for link in links:
                href = link['href']
                full_url = urljoin(current_url, href)  # Construct absolute URL
                
                # Check if the link is internal and hasn't been visited
                if urlparse(full_url).netloc == urlparse(start_url).netloc and full_url not in visited_urls:
                    urls_to_visit.append(full_url)  # Add new links to the list to visit
                    
        except requests.RequestException as e:
            print(f"Error fetching {current_url}: {e}")

    return '\n'.join(all_scraped_content)  # Return only the scraped content

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
    cleaned_text = ''.join(c for c in cleaned_text if c.isalnum() or c.isspace() or c in ",.;:!?")

    return cleaned_text


def main():
    # File path to the Parquet file
    parquet_file_path = './challenge_1/list_of_company_websites.snappy.parquet'  # Replace with your snappy-compressed parquet file path

    # Domain to check in each website
    domain_to_check = 'draftingdesign.com'  
    url_to_check = 'https://' + domain_to_check

    # Read the Parquet data into a DataFrame
    df = read_parquet_file(parquet_file_path)
    
    website_content = scrape_links_and_content(url_to_check)
    cleaned_content = clean_website_content2(website_content)
    #print(website_content)
    save_content_to_notepad(cleaned_content, './challenge_1/' + domain_to_check + '.txt')
    extracted_addresses = extract_pyap(cleaned_content)
    print(extracted_addresses)

if __name__ == "__main__":
    main()
