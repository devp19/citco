import pandas as pd
import base64
import logging
from dashboard import generate_graph_data

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def flip_name(name):
    if "," in name:
        parts = name.split(",")
        return parts[1].strip() + " " + parts[0].strip()
    return name.strip()

def prepare_data(citations_df, grants_df, university=None, time_frame=None):
    try:
        citations_copy = citations_df.copy()
        grants_copy = grants_df.copy()
        
        grants_copy["Flipped Name"] = grants_copy["Name"].apply(flip_name)
        
        citations_copy["Name"] = citations_copy["Name"].str.lower().str.strip()
        citations_copy["Fiscal Year"] = citations_copy["Fiscal Year"].astype(str).str.strip()
        grants_copy["Name"] = grants_copy["Flipped Name"].str.lower().str.strip()
        grants_copy["Fiscal Year"] = grants_copy["Fiscal Year"].astype(str).str.strip()
        
        merged_df = pd.merge(citations_copy, grants_copy, on=["Name", "Fiscal Year"])
        final_df = merged_df[["Name", "University", "Fiscal Year", "CitationCount", "Amount($)"]]
        
        final_df["CitationCount"] = pd.to_numeric(final_df["CitationCount"], errors="coerce")
        final_df["Amount($)"] = pd.to_numeric(final_df["Amount($)"], errors="coerce")
        final_df = final_df.dropna(subset=["CitationCount", "Amount($)"])
        final_df = final_df[(final_df["CitationCount"] >= 0)]
        
        if university and university != 'all':
            final_df = final_df[final_df['University'].str.contains(university, case=False, na=False)]
        
        if time_frame and time_frame != 'all':
            if time_frame == '1y':
                most_recent = final_df['Fiscal Year'].max()
                final_df = final_df[final_df['Fiscal Year'] == most_recent]
            elif time_frame == '3y':
                years = sorted(final_df['Fiscal Year'].unique(), reverse=True)
                if len(years) > 3:
                    years = years[:3]
                final_df = final_df[final_df['Fiscal Year'].isin(years)]
            elif time_frame == '5y':
                years = sorted(final_df['Fiscal Year'].unique(), reverse=True)
                if len(years) > 5:
                    years = years[:5]
                final_df = final_df[final_df['Fiscal Year'].isin(years)]
        
        return final_df
    
    except Exception as e:
        logger.error(f"Error preparing data: {str(e)}")
        raise

def generate_graph(citations_df, grants_df, graph_type, university=None, time_frame=None):
    return generate_graph_data(citations_df, grants_df, graph_type, university, time_frame)
