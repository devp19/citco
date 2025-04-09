from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import io
import base64
import logging
from utils import generate_graph, prepare_data

matplotlib.use('Agg')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

app.static_folder = 'static'

try:
    citations_df = pd.read_csv("SCHOLAR.csv", header=None)
    citations_df.columns = ["Name", "University", "Fiscal Year", "CitationWindow", "CitationCount"]
    
    grants_df = pd.read_csv("NSERC.csv")
    
    logger.info(f"Citations data loaded: {len(citations_df)} records")
    logger.info(f"Grants data loaded: {len(grants_df)} records")
    
    universities = citations_df['University'].dropna().unique().tolist()
    universities = [uni for uni in universities if uni != 'NOT_FOUND']
    universities.sort()
    
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
        
        img_data = generate_graph(citations_df, grants_df, graph_type, university, time_frame)
        return jsonify({'image': img_data})
        
    except Exception as e:
        logger.error(f"Error generating graph: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/data/summary')
def get_data_summary():
    try:
        university = request.args.get('university', 'all')
        time_frame = request.args.get('timeframe', 'all')
        
        df = prepare_data(citations_df, grants_df, university, time_frame)
        
        stats = {
            'total_citations': int(df['CitationCount'].sum()),
            'total_grants': int(df['Amount($)'].sum()),
            'avg_citations': round(df['CitationCount'].mean(), 2),
            'avg_grants': round(df['Amount($)'].mean(), 2),
            'researchers_count': df['Name'].nunique()
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error calculating summary stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
