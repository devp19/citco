let currentGraphType = 'citation_vs_grants';
let isFullscreen = false;

const chartTitles = {
    'citation_vs_grants': 'Citation Count vs Grant Amount',
    'avg_citations': 'Average Citation Count Over Time',
    'avg_grants': 'Average Grant Amount Over Time'
};

document.addEventListener('DOMContentLoaded', function() {
    const graphImg = document.getElementById('graph-img');
    const chartTitle = document.getElementById('chart-title');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    const exitFullscreenBtn = document.getElementById('exitFullscreenBtn');
    const chartArea = document.getElementById('chartArea');
    const loadingOverlay = document.getElementById('loading-overlay');

    document.getElementById('change-chart-btn').addEventListener('click', function() {
        if (currentGraphType === 'citation_vs_grants') {
            currentGraphType = 'avg_citations';
        } else if (currentGraphType === 'avg_citations') {
            currentGraphType = 'avg_grants';
        } else {
            currentGraphType = 'citation_vs_grants';
        }
        
        chartTitle.textContent = chartTitles[currentGraphType];
        
        fetchGraph();
    });

    function toggleFullscreen(enterFullscreen) {
        isFullscreen = enterFullscreen;
        chartArea.classList.toggle('fullscreen', isFullscreen);
        
        if (isFullscreen) {
            exitFullscreenBtn.style.display = 'block';
            fullscreenBtn.innerHTML = '&#x26F6; Fullscreen';
        } else {
            exitFullscreenBtn.style.display = 'none';
        }
    }
    
    fullscreenBtn.addEventListener('click', function() {
        toggleFullscreen(true);
    });
    
    exitFullscreenBtn.addEventListener('click', function() {
        toggleFullscreen(false);
    });

    document.getElementById('university-select').addEventListener('change', function() {
        fetchGraph();
        fetchSummaryStats();
    });

    document.getElementById('timeframe-select').addEventListener('change', function() {
        fetchGraph();
        fetchSummaryStats();
    });

    fetchGraph();
    fetchSummaryStats();
});

function fetchGraph() {
    const loadingOverlay = document.getElementById('loading-overlay');
    const graphImg = document.getElementById('graph-img');
    
    loadingOverlay.style.display = 'flex';
    
    const university = document.getElementById('university-select').value;
    const timeframe = document.getElementById('timeframe-select').value;
    
    fetch(`/graph?type=${currentGraphType}&university=${university}&timeframe=${timeframe}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching graph:', data.error);
                graphImg.src = '';
                graphImg.alt = 'Error loading graph';
                const errorText = document.createElement('div');
                errorText.className = 'error-message';
                errorText.textContent = 'Error loading graph: ' + data.error;
                document.getElementById('chart-container').appendChild(errorText);
            } else {
                graphImg.src = 'data:image/png;base64,' + data.image;
                graphImg.alt = chartTitles[currentGraphType];
                
                const errorMessages = document.getElementsByClassName('error-message');
                while (errorMessages.length > 0) {
                    errorMessages[0].parentNode.removeChild(errorMessages[0]);
                }
            }
            
            loadingOverlay.style.display = 'none';
        })
        .catch(error => {
            console.error('Error:', error);
            loadingOverlay.style.display = 'none';
        });
}

function fetchSummaryStats() {
    const university = document.getElementById('university-select').value;
    const timeframe = document.getElementById('timeframe-select').value;
    
    fetch('/data/total_grants')
        .then(response => response.json())
        .then(totalData => {
            const totalGrantsAll = totalData.total_grants;
            
            fetch(`/data/summary?university=${university}&timeframe=${timeframe}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error fetching summary stats:', data.error);
                    } else {
                        document.getElementById('total-citations').textContent = data.total_citations.toLocaleString();
                        
                        if (data.total_grants_original && (university !== 'all' || timeframe !== 'all')) {
                            document.getElementById('total-grants').textContent = '$' + data.total_grants_original.toLocaleString();
                        } else if (totalGrantsAll) {
                            document.getElementById('total-grants').textContent = '$' + totalGrantsAll.toLocaleString();
                        } else {
                            document.getElementById('total-grants').textContent = '$' + data.total_grants.toLocaleString();
                        }
                        
                        document.getElementById('avg-citations').textContent = data.avg_citations.toLocaleString();
                        document.getElementById('avg-grants').textContent = '$' + data.avg_grants.toLocaleString();
                        document.getElementById('researchers-count').textContent = data.researchers_count.toLocaleString();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        })
        .catch(error => {
            console.error('Error fetching total grants:', error);
            
            fetch(`/data/summary?university=${university}&timeframe=${timeframe}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error fetching summary stats:', data.error);
                    } else {
                        document.getElementById('total-citations').textContent = data.total_citations.toLocaleString();
                        document.getElementById('total-grants').textContent = '$' + data.total_grants.toLocaleString();
                        document.getElementById('avg-citations').textContent = data.avg_citations.toLocaleString();
                        document.getElementById('avg-grants').textContent = '$' + data.avg_grants.toLocaleString();
                        document.getElementById('researchers-count').textContent = data.researchers_count.toLocaleString();
                    }
                });
        });
}