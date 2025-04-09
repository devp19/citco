import pandas as pd
df = pd.read_csv("NSERC.csv")
total = df["Amount($)"].sum()
print(f"Number of records: {len(df)}")
print(f"Total grant amount: ${total:,.0f}")
