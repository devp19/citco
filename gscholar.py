import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import csv
import os
import random
from urllib.parse import quote

def get_headers():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://scholar.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def read_nserc_data(file_path):
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            exit(1)
    elif file_path.endswith('.csv'):
        try:
            return pd.read_csv(file_path, sep=',', quotechar='"')
        except Exception as e:
            try:
                return pd.read_csv(file_path, sep=',', quotechar='"', escapechar='\\')
            except Exception as e2:
                print(f"Error reading CSV file: {e2}")
                exit(1)
    else:
        print(f"Unsupported file format: {file_path}")
        exit(1)

input_file = "NSERC_DATASET.xlsx" 
output_file = "researcher_citations.csv"

print(f"Reading input file: {input_file}")
df = read_nserc_data(input_file)

# print("First 5 rows of input data:")
# print(df.head())

if 'Name' in df.columns:
    df['Name'] = df['Name'].str.replace('"', '').str.strip()
    print("Cleaned 'Name' column")
else:
    print(f"Warning: 'Name' column not found in {list(df.columns)}")
    exit(1)

if not os.path.exists(output_file):
    with open(output_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "University", "Fiscal Year", "CitationWindow", "CitationCount"])
    print(f"Created new output file: {output_file}")

processed_names = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            next(reader)  
            for row in reader:
                if row and len(row) >= 3:  
                    name = row[0]  
                    fiscal_year = row[2]  
                   
                    name_year_key = f"{name}_{fiscal_year}"
                    processed_names.add(name_year_key)
        except StopIteration:
            print("Output file exists but appears to be empty or contains only a header.")
    print(f"found {len(processed_names)} previously processed entries")

grouped = df.groupby(["Name", "Fiscal Year"]).first().reset_index()
print(f"Total unique Name/Fiscal Year combinations: {len(grouped)}")

CHUNK_SIZE = 25
chunk_start = 350  # change this part on reruns -->>>>>> terminal will say next chunk value put that number here pls!!!! (e.g., 25, 50, 75...)
chunk_end = min(chunk_start + CHUNK_SIZE, len(grouped))
chunk = grouped.iloc[chunk_start:chunk_end]
print(f"Processing chunk from {chunk_start} to {chunk_end-1} ({len(chunk)} entries)")

def search_author(name):
    search_url = f"https://scholar.google.com/citations?view_op=search_authors&mauthors={quote(name)}"
    
    response = requests.get(search_url, headers=get_headers())
    if response.status_code != 200:
        print(f"search request failed with status code {response.status_code}")
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    profile_links = soup.select('a[href*="user="]')
    
    if not profile_links:
        return None
    
    author_id = profile_links[0]['href'].split('user=')[1].split('&')[0]
    return author_id

def get_author_profile(author_id):
    profile_url = f"https://scholar.google.com/citations?user={author_id}&hl=en"
    
    response = requests.get(profile_url, headers=get_headers())
    if response.status_code != 200:
        print(f"profile req failed with status code {response.status_code}")
        raise Exception(f"failed to fetch profile: {response.status_code}")
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    name_elem = soup.select_one('#gsc_prf_in')
    affiliation_elem = soup.select_one('.gsc_prf_il')
    
    name = name_elem.text if name_elem else "N/A"
    affiliation = affiliation_elem.text if affiliation_elem else "UNKNOWN"
    
    return {
        "name": name,
        "affiliation": affiliation
    }

def get_publications_in_range(author_id, year_start, year_end):
    publications_url = f"https://scholar.google.com/citations?user={author_id}&hl=en&cstart=0&pagesize=100"
    
    response = requests.get(publications_url, headers=get_headers())
    if response.status_code != 200:
        print(f"publications request failed with status code {response.status_code}")
        raise Exception(f"failed to fetch publications: {response.status_code}")
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    total_citations = 0
    
    pub_rows = soup.select('tr.gsc_a_tr')
    
    for row in pub_rows:
        year_elem = row.select_one('.gsc_a_y')
        if not year_elem or not year_elem.text:
            continue
            
        try:
            year = int(year_elem.text)
            if year_start <= year <= year_end:
                citation_elem = row.select_one('.gsc_a_c')
                if citation_elem and citation_elem.text and citation_elem.text.strip().isdigit():
                    total_citations += int(citation_elem.text)
        except ValueError:
            continue
    
    return total_citations

for index, row in chunk.iterrows():
    name = row["Name"]
    fiscal_year = row["Fiscal Year"]
    
    original_name_year_key = f"{name}_{fiscal_year}"
    
    if original_name_year_key in processed_names:
        print(f"skipping already processed name: {name} for {fiscal_year}")
        continue
    
    print(f"📋 Processing {name} for {fiscal_year}")
    
    time.sleep(random.uniform(5, 10))
    
    try:
        author_id = search_author(name)
        
        if not author_id:
            print(f"no corresponding author found for {name}. moving to next...")
            
            with open(output_file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([name, "NOT_FOUND", fiscal_year, "N/A", -1])
            
            processed_names.add(original_name_year_key)
            continue
        
        year_parts = fiscal_year.split("-")
        if len(year_parts) == 2:
            year_start = int(year_parts[0]) - 6
            year_end = int(year_parts[0]) - 1
        else:
            year_start = int(fiscal_year) - 6
            year_end = int(fiscal_year) - 1
            
        citation_window = f"{year_start}-{year_end}"
        
        profile_data = get_author_profile(author_id)
        name_clean = profile_data["name"]
        affiliation = profile_data["affiliation"]
        
        total_citations = get_publications_in_range(author_id, year_start, year_end)
        
        with open(output_file, "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([name_clean, affiliation, fiscal_year, citation_window, total_citations])
        
        processed_names.add(original_name_year_key)
        
        print(f"Success: {name_clean} | {affiliation} | {citation_window} → {total_citations} citations")
        
        time.sleep(random.uniform(30, 45))
        
    except Exception as e:
        print(f"error with {name}: {str(e)}")
        print("waiting")
        time.sleep(random.uniform(300, 600)) 
        
        try:
            university = row.get('University', '') if 'University' in row else ''
            search_query = f"{name} {university}"
            
            print(f"alternate search regex test: {search_query}")
            
            with open(output_file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([name, "ERROR", fiscal_year, "N/A", -1])
            
            processed_names.add(original_name_year_key)
            
        except Exception as e2:
            print(f"second attemp failed for {name}: {str(e2)}")
            
            with open(output_file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([name, "ERROR", fiscal_year, "N/A", -1])
            
            processed_names.add(original_name_year_key)
            
            time.sleep(random.uniform(600, 900)) 

print(f"\n✅ Done! Results saved to {output_file}")
print(f"Processed {len(chunk)} entries from chunk {chunk_start} to {chunk_end-1}")
print(f"Next chunk start value: {chunk_end}")