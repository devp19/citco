import pandas as pd
from scholarly import scholarly
import time

# Load your dataset
df = pd.read_excel("NSERC_FILTERED_DATASET.xlsx")

# Prepare output file
output_file = "researcher_affiliations.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("Name, University\n")

# Loop through names
names = df["Name"].dropna().unique()

for name in names:
    try:
        print(f"Searching for: {name}")
        search = scholarly.search_author(name)
        author = next(search)
        filled_author = scholarly.fill(author)

        name_clean = filled_author.get("name", "N/A")
        affiliation = filled_author.get("affiliation", "N/A")

        line = f"Name: {name_clean}, University: {affiliation}"
        print(line)

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name_clean}, {affiliation}\n")

        time.sleep(2)  # To avoid being rate-limited

    except Exception as e:
        print(f"Error with {name}: {e}")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name}, NOT FOUND\n")
        continue

print(f"\n✅ Done! Saved results to {output_file}")
