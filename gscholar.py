from scholarly import scholarly
import pandas as pd
import time
import csv
import os

df = pd.read_excel("NSERC_FILTERED_DATASET.xlsx")

output_file = "researcher_citations.csv"
if not os.path.exists(output_file):
    with open(output_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "University", "Fiscal Year", "CitationWindow", "CitationCount"])

processed_names = set()
with open(output_file, "r", encoding="utf-8") as f:
    next(f)
    for line in f:
        name = line.strip().split(",")[0]
        processed_names.add(name)

grouped = df.groupby(["Name", "Fiscal Year"]).first().reset_index()

CHUNK_SIZE = 25
chunk_start = 0  # change this part (I will tell u depending on size of output csv) on reruns --> (e.g., 25, 50, 75...)
chunk = grouped.iloc[chunk_start:chunk_start + CHUNK_SIZE]

for index, row in chunk.iterrows():
    name = row["Name"]
    fiscal_year = row["Fiscal Year"]

    if name in processed_names:
        print(f"⏩ Skipping already processed: {name}")
        continue

    while True:
        try:
            if index % 10 == 0:
                print("📡 Checking Google Scholar availability...")
                test = next(scholarly.search_author("Yoshua Bengio"))
                if not test:
                    raise Exception("Rate limit triggered")

            print(f"🔍 Searching: {name}")
            search = scholarly.search_author(name)
            author = next(search)
            filled_author = scholarly.fill(author)

            name_clean = filled_author.get("name", "N/A")
            affiliation = filled_author.get("affiliation", "UNKNOWN")

            year_start = int(fiscal_year.split("-")[0]) - 6
            year_end = int(fiscal_year.split("-")[0]) - 1
            citation_window = f"{year_start}-{year_end}"

            total_citations = 0
            if "publications" in filled_author:
                for pub in filled_author["publications"]:
                    try:
                        pub_filled = scholarly.fill(pub)
                        pub_year = pub_filled.get("bib", {}).get("pub_year", None)
                        if pub_year and year_start <= int(pub_year) <= year_end:
                            total_citations += pub_filled.get("num_citations", 0)
                    except Exception:
                        continue

            with open(output_file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([name_clean, affiliation, fiscal_year, citation_window, total_citations])

            print(f"worked thanks: {name_clean} | {affiliation} | {citation_window} → {total_citations} citations")
            time.sleep(15)  # small pause 
            break 

        except Exception as e:
            print(f"rate-limit or error with {name}: {e}")
            print("wait 15 minutes before retrying...")
            time.sleep(900)  # 15-minute wait for ip ban rate-limit :(
            continue

print(f"\ndone, results saved to {output_file}")
