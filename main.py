from flask import Flask, render_template, jsonify, request, send_from_directory
import os
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

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

app.static_folder = 'static'

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
        
        merged_df = pd.merge(citations_df, grants_df, on=["Name", "Fiscal Year"], suffixes=('_citation', '_grant'))
        
        final_df = merged_df[["Name", "University", "Fiscal Year", "CitationCount", "Amount($)"]]
        
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
        elif time_frame == '6y':
            years = sorted(filtered_df['Fiscal Year'].unique(), reverse=True)
            if len(years) > 6:
                years = years[:6]
            filtered_df = filtered_df[filtered_df['Fiscal Year'].isin(years)]
        elif time_frame == '10y':
            years = sorted(filtered_df['Fiscal Year'].unique(), reverse=True)
            if len(years) > 10:
                years = years[:10]
            filtered_df = filtered_df[filtered_df['Fiscal Year'].isin(years)]
    
    return filtered_df

def create_citation_vs_grants_graph(df):
    plt.style.use('seaborn-v0_8-darkgrid')
    
    primary_color = "#eb5e28" 
    secondary_color = "#252422" 
    bg_color = "#F2EAD3"  
    
    fig, ax = plt.subplots(facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    ax.scatter(df["CitationCount"], df["Amount($)"], alpha=0.7, color=primary_color, edgecolor=secondary_color)
    
    if len(df) > 1:
        z = np.polyfit(df["CitationCount"], df["Amount($)"], 1)
        p = np.poly1d(z)
        ax.plot(df["CitationCount"], p(df["CitationCount"]), linestyle='--', color=secondary_color, linewidth=2, alpha=0.8)
    
    ax.set_xlabel("Citation Count (5-Year Window)", color=secondary_color, fontweight='bold')
    ax.set_ylabel("Grant Amount ($)", color=secondary_color, fontweight='bold')
    ax.set_title("Citation Count vs Grant Amount", color=secondary_color, fontsize=14, fontweight='bold')
    
    ax.grid(True, linestyle='--', alpha=0.4, color=secondary_color)
    
    ax.tick_params(colors=secondary_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(secondary_color)
    
    fig.tight_layout()
    
    return fig

def create_avg_citations_graph(df):
    plt.style.use('seaborn-v0_8-darkgrid')
    
    primary_color = "#2a9d8f"  
    secondary_color = "#252422"  
    bg_color = "#F2EAD3"  
    
    graph_data = df.groupby("Fiscal Year")["CitationCount"].mean().reset_index()
    graph_data = graph_data.sort_values("Fiscal Year")
    
    fig, ax = plt.subplots(facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    ax.plot(graph_data["Fiscal Year"], graph_data["CitationCount"], 
            linestyle='-', marker='o', linewidth=2.5, 
            color=primary_color, markeredgecolor=secondary_color,
            markerfacecolor=primary_color, markersize=8)
    
    ax.set_xlabel("Fiscal Year", color=secondary_color, fontweight='bold')
    ax.set_ylabel("Average Citation Count", color=secondary_color, fontweight='bold')
    ax.set_title("Average Citation Count Over Time", color=secondary_color, fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45, colors=secondary_color)
    ax.tick_params(axis='y', colors=secondary_color)
    
    ax.grid(True, linestyle='--', alpha=0.4, color=secondary_color)
    
    for spine in ax.spines.values():
        spine.set_edgecolor(secondary_color)
    
    for x, y in zip(graph_data["Fiscal Year"], graph_data["CitationCount"]):
        ax.annotate(f"{y:.1f}", (x, y), 
                   textcoords="offset points", 
                   xytext=(0,10), 
                   ha='center',
                   color=secondary_color,
                   fontweight='bold')
    
    fig.tight_layout()
    
    return fig

def create_avg_grants_graph(df):
    plt.style.use('seaborn-v0_8-darkgrid')
    
    primary_color = "#D88C00"  
    secondary_color = "#252422"  
    bg_color = "#F2EAD3" 
    
    graph_data = df.groupby("Fiscal Year")["Amount($)"].mean().reset_index()
    graph_data = graph_data.sort_values("Fiscal Year")
    
    fig, ax = plt.subplots(facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    ax.plot(graph_data["Fiscal Year"], graph_data["Amount($)"], 
            linestyle='-', marker='o', linewidth=2.5, 
            color=primary_color, markeredgecolor=secondary_color,
            markerfacecolor=primary_color, markersize=8)
    
    ax.set_xlabel("Fiscal Year", color=secondary_color, fontweight='bold')
    ax.set_ylabel("Average Grant Amount ($)", color=secondary_color, fontweight='bold')
    ax.set_title("Average Grant Amount Over Time", color=secondary_color, fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45, colors=secondary_color)
    ax.tick_params(axis='y', colors=secondary_color)
    
    ax.grid(True, linestyle='--', alpha=0.4, color=secondary_color)
    
    for spine in ax.spines.values():
        spine.set_edgecolor(secondary_color)
    
    for x, y in zip(graph_data["Fiscal Year"], graph_data["Amount($)"]):
        ax.annotate(f"${y:.0f}", (x, y), 
                   textcoords="offset points", 
                   xytext=(0,10), 
                   ha='center',
                   color=secondary_color,
                   fontweight='bold')
    
    fig.tight_layout()
    
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
        
        bg_color = "#F2EAD3"  
        text_color = "#252422"  
        

        if filtered_df.empty:
            logger.warning("No data available after filtering")
            fig, ax = plt.subplots(facecolor=bg_color)
            ax.set_facecolor(bg_color)
            ax.text(0.5, 0.5, "No data available for the selected filters", 
                    horizontalalignment='center', verticalalignment='center', 
                    transform=ax.transAxes, fontsize=14, fontweight='bold',
                    color=text_color)
            return fig_to_base64(fig)
        
        if graph_type == 'citation_vs_grants':
            fig = create_citation_vs_grants_graph(filtered_df)
        elif graph_type == 'avg_citations':
            fig = create_avg_citations_graph(filtered_df)
        elif graph_type == 'avg_grants':
            fig = create_avg_grants_graph(filtered_df)
        else:
            logger.warning(f"Unknown graph type: {graph_type}")
            fig, ax = plt.subplots(facecolor=bg_color)
            ax.set_facecolor(bg_color)
            ax.text(0.5, 0.5, f"Unknown graph type: {graph_type}", 
                    horizontalalignment='center', verticalalignment='center', 
                    transform=ax.transAxes, fontsize=14, fontweight='bold',
                    color=text_color)
        
        return fig_to_base64(fig)
    
    except Exception as e:
        logger.error(f"Error generating graph: {str(e)}")
        fig, ax = plt.subplots(facecolor=bg_color)
        ax.set_facecolor(bg_color)
        ax.text(0.5, 0.5, f"Error generating graph: {str(e)}", 
                horizontalalignment='center', verticalalignment='center', 
                transform=ax.transAxes, fontsize=14, fontweight='bold',
                color=text_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(text_color)
        return fig_to_base64(fig)

try:
    citations_df = pd.read_csv("SCHOLAR.csv", header=None)
    citations_df.columns = ["Name", "University", "Fiscal Year", "CitationWindow", "CitationCount"]
    
    grants_df = pd.read_csv("NSERC.csv")
    
    logger.info(f"Citations data loaded: {len(citations_df)} records")
    logger.info(f"Grants data loaded: {len(grants_df)} records")
    
    university_names = [
        "University of Calgary", 
        "University of Regina", 
        "Carleton University", 
        "Simon Fraser University", 
        "University of Alberta", 
        "University of New Brunswick", 
        "University of Waterloo", 
        "Virginia Tech", 
        "West Virginia University", 
        "University of Victoria", 
        "University of Toronto", 
        "Lawrence Berkeley National Laboratory", 
        "ÉTS (U. of Quebec)", 
        "University of Guelph", 
        "Brock University"
    ]
    universities = sorted(university_names)
    
    fiscal_years = citations_df['Fiscal Year'].dropna().unique().tolist()
    fiscal_years.sort(reverse=True)
    
except Exception as e:
    logger.error(f"Error loading data: {str(e)}")
    citations_df = None
    grants_df = None
    universities = []
    fiscal_years = []

@app.route('/')
def index():
    return render_template('index.html', 
                         universities=universities,
                         fiscal_years=fiscal_years)

@app.route('/graph')
def get_graph():
    try:
        graph_type = request.args.get('type', 'citation_vs_grants')
        university = request.args.get('university', 'all')
        time_frame = request.args.get('timeframe', 'all')
        
        logger.debug(f"Graph request - Type: {graph_type}, University: {university}, Time Frame: {time_frame}")
        
        img_data = generate_graph_data(citations_df, grants_df, graph_type, university, time_frame)
        return jsonify({'image': img_data})
        
    except Exception as e:
        logger.error(f"Error generating graph: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/data/summary')
def get_data_summary():
    try:
        university = request.args.get('university', 'all')
        time_frame = request.args.get('timeframe', 'all')
        
        filtered_grants_df = grants_df.copy()
        
        if time_frame and time_frame != 'all':
            if time_frame == '1y':
                most_recent = filtered_grants_df['Fiscal Year'].max()
                filtered_grants_df = filtered_grants_df[filtered_grants_df['Fiscal Year'] == most_recent]
            elif time_frame == '3y':
                years = sorted(filtered_grants_df['Fiscal Year'].unique(), reverse=True)
                if len(years) > 3:
                    years = years[:3]
                filtered_grants_df = filtered_grants_df[filtered_grants_df['Fiscal Year'].isin(years)]
            elif time_frame == '6y':
                years = sorted(filtered_grants_df['Fiscal Year'].unique(), reverse=True)
                if len(years) > 6:
                    years = years[:6]
                filtered_grants_df = filtered_grants_df[filtered_grants_df['Fiscal Year'].isin(years)]
            elif time_frame == '10y':
                years = sorted(filtered_grants_df['Fiscal Year'].unique(), reverse=True)
                if len(years) > 10:
                    years = years[:10]
                filtered_grants_df = filtered_grants_df[filtered_grants_df['Fiscal Year'].isin(years)]
        
        if university and university != 'all':
            grants_with_flipped = grants_df.copy()
            grants_with_flipped["Flipped Name"] = grants_with_flipped["Name"].apply(flip_name)
            grants_with_flipped["Name_Lower"] = grants_with_flipped["Flipped Name"].str.lower().str.strip()
            
            citations_with_uni = citations_df.copy()
            citations_with_uni["Name_Lower"] = citations_with_uni["Name"].str.lower().str.strip()
            
            uni_citations = citations_with_uni[citations_with_uni['University'].str.contains(university, case=False, na=False)]
            
            uni_researchers = set(uni_citations["Name_Lower"].unique())
            
            filtered_grants_df = filtered_grants_df[
                filtered_grants_df["Name"].apply(lambda x: flip_name(x).lower().strip() in uni_researchers)
            ]
        
        total_grants_value = int(filtered_grants_df['Amount($)'].sum())
        avg_grants_value = round(filtered_grants_df['Amount($)'].mean(), 2)
        
        final_df = preprocess_data(citations_df, grants_df)
        filtered_df = filter_data(final_df, university, time_frame)
        
        stats = {
            'total_citations': int(filtered_df['CitationCount'].sum()),
            'total_grants': total_grants_value,
            'avg_citations': round(filtered_df['CitationCount'].mean(), 2),
            'avg_grants': avg_grants_value,
            'researchers_count': filtered_df['Name'].nunique()
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error calculating summary stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)