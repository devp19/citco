import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import io
import base64
import logging

matplotlib.use('Agg')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"figure.figsize": (10, 6), "axes.titlesize": 14, "axes.labelsize": 12})

def flip_name(name):
    if "," in name:
        parts = name.split(",")
        return parts[1].strip() + " " + parts[0].strip()
    return name.strip()

def preprocess_data(citations_df, grants_df):
    try:
        citations_df = citations_df.copy()
        grants_df = grants_df.copy()
        
        grants_df["Flipped Name"] = grants_df["Name"].apply(flip_name)
        
        citations_df["Name"] = citations_df["Name"].str.lower().str.strip()
        citations_df["Fiscal Year"] = citations_df["Fiscal Year"].astype(str).str.strip()
        grants_df["Name"] = grants_df["Flipped Name"].str.lower().str.strip()
        grants_df["Fiscal Year"] = grants_df["Fiscal Year"].astype(str).str.strip()
        
        merged_df = pd.merge(citations_df, grants_df, on=["Name", "Fiscal Year"])
        final_df = merged_df[["Name", "University_x", "Fiscal Year", "CitationCount", "Amount($)"]]
        final_df.rename(columns={"University_x": "University"}, inplace=True)
        
        final_df["CitationCount"] = pd.to_numeric(final_df["CitationCount"], errors="coerce")
        final_df["Amount($)"] = pd.to_numeric(final_df["Amount($)"], errors="coerce")
        final_df = final_df.dropna(subset=["CitationCount", "Amount($)"])
        final_df = final_df[(final_df["CitationCount"] >= 0)]
        
        return final_df
    except Exception as e:
        logger.error(f"Error preprocessing data: {str(e)}")
        raise

def filter_data(df, university=None, time_frame=None):
    filtered_df = df.copy()
    
    if university and university != 'all':
        filtered_df = filtered_df[filtered_df['University'].str.contains(university, case=False, na=False)]
    
    if time_frame and time_frame != 'all':
        if time_frame == '1y':
            most_recent = filtered_df['Fiscal Year'].max()
            filtered_df = filtered_df[filtered_df['Fiscal Year'] == most_recent]
        elif time_frame == '3y':
            years = sorted(filtered_df['Fiscal Year'].unique(), reverse=True)
            if len(years) > 3:
                years = years[:3]
            filtered_df = filtered_df[filtered_df['Fiscal Year'].isin(years)]
        elif time_frame == '5y':
            years = sorted(filtered_df['Fiscal Year'].unique(), reverse=True)
            if len(years) > 5:
                years = years[:5]
            filtered_df = filtered_df[filtered_df['Fiscal Year'].isin(years)]
    
    return filtered_df

def create_citation_vs_grants_graph(df):
    fig, ax = plt.subplots()
    
    ax.scatter(df["CitationCount"], df["Amount($)"], alpha=0.6)
    
    if len(df) > 1:
        z = np.polyfit(df["CitationCount"], df["Amount($)"], 1)
        p = np.poly1d(z)
        ax.plot(df["CitationCount"], p(df["CitationCount"]), "r--", alpha=0.8)
    
    ax.set_xlabel("Citation Count (5-Year Window)")
    ax.set_ylabel("Grant Amount ($)")
    ax.set_title("Citation Count vs Grant Amount")
    
    ax.grid(True, linestyle='--', alpha=0.7)
    
    return fig

def create_avg_citations_graph(df):
    graph_data = df.groupby("Fiscal Year")["CitationCount"].mean().reset_index()
    graph_data = graph_data.sort_values("Fiscal Year")
    
    fig, ax = plt.subplots()
    ax.plot(graph_data["Fiscal Year"], graph_data["CitationCount"], linestyle='-', marker='o')
    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("Average Citation Count")
    ax.set_title("Average Citation Count Over Time")
    ax.tick_params(axis='x', rotation=45)
    
    ax.grid(True, linestyle='--', alpha=0.7)
    
    for x, y in zip(graph_data["Fiscal Year"], graph_data["CitationCount"]):
        ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    return fig

def create_avg_grants_graph(df):
    graph_data = df.groupby("Fiscal Year")["Amount($)"].mean().reset_index()
    graph_data = graph_data.sort_values("Fiscal Year")
    
    fig, ax = plt.subplots()
    ax.plot(graph_data["Fiscal Year"], graph_data["Amount($)"], linestyle='-', marker='o', color="orange")
    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("Average Grant Amount ($)")
    ax.set_title("Average Grant Amount Over Time")
    ax.tick_params(axis='x', rotation=45)
    
    ax.grid(True, linestyle='--', alpha=0.7)
    
    for x, y in zip(graph_data["Fiscal Year"], graph_data["Amount($)"]):
        ax.annotate(f"${y:.0f}", (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    return fig

def fig_to_base64(fig):
    img_buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(img_buf, format='png', dpi=100)
    img_buf.seek(0)
    img_data = base64.b64encode(img_buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return img_data

def generate_graph_data(citations_df, grants_df, graph_type='citation_vs_grants', university=None, time_frame=None):
    try:
        final_df = preprocess_data(citations_df, grants_df)
        
        filtered_df = filter_data(final_df, university, time_frame)
        
        if filtered_df.empty:
            logger.warning("No data available after filtering")
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No data available for the selected filters", 
                    horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
            return fig_to_base64(fig)
        
        if graph_type == 'citation_vs_grants':
            fig = create_citation_vs_grants_graph(filtered_df)
        elif graph_type == 'avg_citations':
            fig = create_avg_citations_graph(filtered_df)
        elif graph_type == 'avg_grants':
            fig = create_avg_grants_graph(filtered_df)
        else:
            logger.warning(f"Unknown graph type: {graph_type}")
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, f"Unknown graph type: {graph_type}", 
                    horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        
        return fig_to_base64(fig)
    
    except Exception as e:
        logger.error(f"Error generating graph: {str(e)}")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f"Error generating graph: {str(e)}", 
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        return fig_to_base64(fig)

if __name__ == "__main__":
    try:
        citations_df = pd.read_csv("SCHOLAR.csv", header=None)
        citations_df.columns = ["Name", "University", "Fiscal Year", "CitationWindow", "CitationCount"]
        
        grants_df = pd.read_csv("NSERC.csv")
        
        citation_vs_grants_img = generate_graph_data(citations_df, grants_df, 'citation_vs_grants')
        avg_citations_img = generate_graph_data(citations_df, grants_df, 'avg_citations')
        avg_grants_img = generate_graph_data(citations_df, grants_df, 'avg_grants')
        
        print("Graph generation test successful")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
