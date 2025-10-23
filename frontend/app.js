// Application State
let map = null;
let currentRoute = null;
let vesselMarker = null;
let routeLayers = [];
let agentIntervals = [];
let journeyInProgress = false;
let journeyInterval = null;
let currentProgress = 0;
let journeyStartDate = null;
let deviationDetected = false;
let journeyPaused = false;
let pausedStep = 0;

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updateDateTime();
    setInterval(updateDateTime, 1000);
});

// Event Listeners
function initializeEventListeners() {
    // Start button
    document.getElementById('startBtn').addEventListener('click', () => {
        animateScreenTransition('welcomeScreen', 'loginScreen');
    });

    // Login form
    document.getElementById('loginForm').addEventListener('submit', (e) => {
        e.preventDefault();
        handleLogin();
    });

    // Configuration form
    document.getElementById('configForm').addEventListener('submit', (e) => {
        e.preventDefault();
        handleConfiguration();
    });

    // Start forecast button
    document.getElementById('startForecastBtn').addEventListener('click', startForecast);

    // Toggle logs
    document.getElementById('toggleLogs').addEventListener('click', () => {
        document.getElementById('agentLogs').classList.toggle('expanded');
    });

    // Tool items click handlers
    document.querySelectorAll('.tool-item').forEach(tool => {
        tool.addEventListener('click', (e) => {
            const toolName = e.currentTarget.dataset.tool;
            const agentName = e.currentTarget.closest('.agent-card').dataset.agent;
            showToolOutput(agentName, toolName);
        });
    });

    // Route selection buttons
    document.querySelectorAll('.btn-select-route').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const routeNum = e.currentTarget.closest('.route-option').dataset.route;
            selectRoute(routeNum);
        });
    });
}

// Screen Transitions
function animateScreenTransition(fromScreen, toScreen) {
    const from = document.getElementById(fromScreen);
    const to = document.getElementById(toScreen);
    
    from.style.animation = 'slideUp 0.5s ease';
    setTimeout(() => {
        from.classList.remove('active');
        to.classList.add('active');
    }, 500);
}

// Login Handler
function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    document.getElementById('loginBtnText').style.display = 'none';
    document.querySelector('.login-loader').style.display = 'block';
    
    // Simulate authentication
    setTimeout(() => {
        animateScreenTransition('loginScreen', 'dashboardScreen');
    }, 3000);
}

// Configuration Handler
function handleConfiguration() {
    const shipmentId = document.getElementById('shipmentId').value;
    const originPort = document.getElementById('originPort').value;
    const destPort = document.getElementById('destPort').value;
    const arrivalDate = document.getElementById('arrivalDate').value;
    
    // Validate hardcoded values
    if (originPort === 'boston' && destPort === 'porto' && arrivalDate === '2025-11-03') {
        showLoading('Initializing AI Analysis...');
        
        setTimeout(() => {
            hideLoading();
            document.getElementById('configView').classList.remove('active');
            document.getElementById('mainView').classList.add('active');
            initializeMap();
            initializeAgentLogs();
        }, 3000);
    } else {
        alert('Please select: Origin: Boston, Destination: Porto, Date: November 3, 2025');
    }
}

// Initialize Map
function initializeMap() {
    // Initialize Leaflet map
    map = L.map('map').setView([40, -40], 4);
    
    // Add dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    // Define ports
    const boston = [42.3601, -71.0589];
    const porto = [41.1579, -8.6291];

    // Add port markers
    L.marker(boston, {
        icon: L.divIcon({
            html: '<i class="fas fa-anchor" style="color: #3b82f6; font-size: 24px;"></i>',
            iconSize: [24, 24],
            className: 'port-marker'
        })
    }).addTo(map).bindPopup('<b>Boston Port</b><br>Origin');

    L.marker(porto, {
        icon: L.divIcon({
            html: '<i class="fas fa-anchor" style="color: #ef4444; font-size: 24px;"></i>',
            iconSize: [24, 24],
            className: 'port-marker'
        })
    }).addTo(map).bindPopup('<b>Porto</b><br>Destination');

    // Draw three routes with 2 intermediate points each (3 sections)
    drawRoutes(boston, porto);

    // Add vessel marker at origin
    vesselMarker = L.marker(boston, {
        icon: L.divIcon({
            html: '<div class="vessel-icon"><i class="fas fa-ship" style="color: #10b981; font-size: 20px;"></i><span style="font-size: 10px; display: block;">MV Atlantic Pioneer</span></div>',
            iconSize: [60, 30],
            className: 'vessel-marker'
        })
    }).addTo(map).bindPopup('<b>MV Atlantic Pioneer</b><br>Container Ship<br>Current Position: Section A');
}

// Draw Maritime Routes with 2 intermediate points (3 sections)
function drawRoutes(boston, porto) {
    // Route 1: Northern Atlantic - 2 intermediate points
    const route1 = [
        boston,
        [44.5, -50],    // Section A end
        [43, -25],      // Section B end
        porto
    ];

    // Route 2: Mid-Atlantic (Recommended) - 2 intermediate points
    const route2 = [
        boston,
        [41, -48],      // Section A end
        [41, -25],      // Section B end
        porto
    ];

    // Route 3: Southern Atlantic - 2 intermediate points
    const route3 = [
        boston,
        [38, -50],      // Section A end
        [39, -25],      // Section B end
        porto
    ];

    // Draw routes
    const routes = [
        { points: route1, color: '#3b82f6', name: 'Route 1: Northern Atlantic' },
        { points: route2, color: '#10b981', name: 'Route 2: Mid-Atlantic' },
        { points: route3, color: '#f59e0b', name: 'Route 3: Southern Atlantic' }
    ];

    routes.forEach((route, index) => {
        const polyline = L.polyline(route.points, {
            color: route.color,
            weight: 3,
            opacity: 0.7,
            dashArray: '10, 10'
        }).addTo(map);
        
        routeLayers.push(polyline);

        // Add intermediate waypoint markers (only 2 points)
        route.points.slice(1, -1).forEach((point, i) => {
            L.marker(point, {
                icon: L.divIcon({
                    html: `<div style="background: ${route.color}; width: 10px; height: 10px; border-radius: 50%;"></div>`,
                    iconSize: [10, 10],
                    className: 'waypoint-marker'
                })
            }).addTo(map).bindPopup(`${route.name}<br>Section ${String.fromCharCode(65 + i)} End`);
        });
    });
}

// Start Forecast Process
function startForecast() {
    const btn = document.getElementById('startForecastBtn');
    btn.style.display = 'none';
    
    showLoading('Initializing Forecast Agents...');
    
    // Start agent activities
    activateAgent('forecast');
    appendLog('[2025-10-22 14:32:01] Forecast Agent: Initializing weather analysis module...');
    
    setTimeout(() => {
        activateAgent('detection');
        appendLog('[2025-10-22 14:32:03] Detection Agent: Connecting to vessel tracking system...');
        appendLog('[2025-10-22 14:32:04] Detection Agent: Retrieving real-time vessel position data...');
    }, 2000);
    
    setTimeout(() => {
        activateAgent('analysis');
        appendLog('[2025-10-22 14:32:06] Analysis Agent: Starting comprehensive route analysis...');
        document.getElementById('deviationDiagram').style.display = 'block';
    }, 4000);
    
    setTimeout(() => {
        activateAgent('resolution');
        activateAgent('portmonitor');
        activateAgent('communication');
        appendLog('[2025-10-22 14:32:08] Resolution Agent: Evaluating optimization strategies...');
        appendLog('[2025-10-22 14:32:09] Port Monitor Agent: Checking Porto port status...');
        appendLog('[2025-10-22 14:32:10] Communication Agent: Standing by for notifications...');
    }, 6000);
    
    // Show results after 5 seconds
    setTimeout(() => {
        hideLoading();
        showForecastResults();
        deactivateAllAgents();
    }, 8000);
}

// Agent Management
function activateAgent(agentName) {
    const status = document.getElementById(`${agentName}Status`);
    if (status) {
        status.textContent = 'Running';
        status.classList.add('running');
    }
    
    // Add specific logs for each agent
    const agentLogs = {
        forecast: [
            'Loading weather models...',
            'Analyzing Atlantic weather patterns...',
            'Processing marine traffic data...',
            'Generating route recommendations...'
        ],
        detection: [
            'Scanning AIS transponder signals...',
            'Vessel position: 41.2°N, 68.5°W...',
            'Speed: 18.5 knots, Heading: 095°...'
        ],
        analysis: [
            'Evaluating weather impact on routes...',
            'Calculating fuel efficiency metrics...',
            'Assessing traffic congestion levels...'
        ]
    };
    
    if (agentLogs[agentName]) {
        agentLogs[agentName].forEach((log, index) => {
            setTimeout(() => {
                appendLog(`[2025-10-22 14:32:${String(10 + index).padStart(2, '0')}] ${agentName}: ${log}`);
            }, index * 500);
        });
    }
}

function deactivateAllAgents() {
    const agents = ['forecast', 'detection', 'analysis', 'resolution', 'portmonitor', 'communication'];
    agents.forEach(agent => {
        const status = document.getElementById(`${agent}Status`);
        if (status) {
            status.textContent = 'Idle';
            status.classList.remove('running');
        }
    });
}

// Show Forecast Results
function showForecastResults() {
    // Load and display forecast report
    loadForecastReport();
    
    // Show report and route selection sections
    document.getElementById('forecastReport').style.display = 'block';
    document.getElementById('routeSelection').style.display = 'block';
    
    // Update report timestamp
    document.getElementById('reportTime').textContent = new Date().toLocaleString();
    
    // Scroll to report
    document.getElementById('forecastReport').scrollIntoView({ behavior: 'smooth' });
}

// Load Forecast Report Content
async function loadForecastReport() {
    const reportContent = `
        <h3>Executive Summary</h3>
        <p><strong>Recommendation:</strong> Route 2 (Mid-Atlantic) is the optimal choice for shipment CARGO-2025-11-BST-PRT.</p>
        
        <h4>Route Analysis Results:</h4>
        
        <div style="margin: 1rem 0;">
            <h5>Route 1: Northern Atlantic (3,245 nm)</h5>
            <ul>
                <li><strong>Weather:</strong> Storm system developing near 45°N, 50°W. Wave heights 4-6m expected.</li>
                <li><strong>Traffic:</strong> Light vessel traffic, clear passage expected.</li>
                <li><strong>Risk Assessment:</strong> HIGH - Weather conditions may cause 12-18 hour delay.</li>
                <li><strong>Fuel Efficiency:</strong> Reduced by 15% due to adverse conditions.</li>
            </ul>
        </div>
        
        <div style="margin: 1rem 0; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981;">
            <h5>Route 2: Mid-Atlantic (3,180 nm) ⭐ RECOMMENDED</h5>
            <ul>
                <li><strong>Weather:</strong> Favorable conditions throughout journey. Wave heights 1-2m.</li>
                <li><strong>Traffic:</strong> Moderate traffic density, well-managed shipping lanes.</li>
                <li><strong>Risk Assessment:</strong> LOW - Minimal disruption expected.</li>
                <li><strong>Fuel Efficiency:</strong> Optimal consumption rate maintained.</li>
                <li><strong>ETA:</strong> November 3, 2025 14:00 UTC (On schedule)</li>
            </ul>
        </div>
        
        <div style="margin: 1rem 0;">
            <h5>Route 3: Southern Atlantic (3,310 nm)</h5>
            <ul>
                <li><strong>Weather:</strong> Clear conditions, excellent visibility.</li>
                <li><strong>Traffic:</strong> Heavy congestion near Strait of Gibraltar approach.</li>
                <li><strong>Risk Assessment:</strong> MEDIUM - Potential 6-8 hour delay due to traffic.</li>
                <li><strong>Fuel Efficiency:</strong> Additional 130nm increases fuel consumption by 8%.</li>
            </ul>
        </div>
        
        <h4>Port Status:</h4>
        <p>Porto port operating normally. Berth B-7 reserved for arrival. No congestion reported.</p>
        
        <h4>Contingency Recommendations:</h4>
        <ul>
            <li>Monitor storm system development for Route 1</li>
            <li>Maintain communication with Porto port authority</li>
            <li>Update crew on selected route parameters</li>
        </ul>
        
        <p><em>Report generated by Strands Agent Forecast System v2.1</em></p>
    `;
    
    document.getElementById('forecastReportContent').innerHTML = reportContent;
}

// Update Forecast Report with Deviation
function updateReportWithDeviation(currentLat, currentLng, expectedLat, expectedLng) {
    const deviationSection = `
        <div style="margin: 2rem 0; padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; border-radius: 8px;">
            <h4 style="color: #ef4444; margin-bottom: 1rem;">
                <i class="fas fa-exclamation-triangle"></i> Deviation Alert
            </h4>
            <p style="color: #fbbf24; font-weight: 600; margin-bottom: 1rem;">
                Vessel has deviated significantly from designated route coordinates.
            </p>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                <h5 style="color: #cbd5e1; margin-bottom: 0.5rem;">Position Analysis:</h5>
                <table style="width: 100%; color: #94a3b8; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: 0.5rem;"><strong>Current Position:</strong></td>
                        <td style="padding: 0.5rem; color: #fbbf24;">${currentLat.toFixed(4)}°N, ${Math.abs(currentLng).toFixed(4)}°W</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem;"><strong>Expected Position:</strong></td>
                        <td style="padding: 0.5rem; color: #10b981;">${expectedLat.toFixed(4)}°N, ${Math.abs(expectedLng).toFixed(4)}°W</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem;"><strong>Deviation:</strong></td>
                        <td style="padding: 0.5rem; color: #ef4444;">${Math.abs(currentLat - expectedLat).toFixed(2)}° Latitude, ${Math.abs(currentLng - expectedLng).toFixed(2)}° Longitude</td>
                    </tr>
                </table>
            </div>
            <p style="color: #cbd5e1; font-size: 0.9rem;">
                <strong>Impact Assessment:</strong> The vessel's current trajectory has deviated from the optimal route. 
                Immediate root cause analysis recommended to identify contributing factors and determine corrective action.
            </p>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 1rem; font-style: italic;">
                Detected by Detection Agent at ${new Date().toLocaleTimeString('en-US')} UTC
            </p>
        </div>
    `;
    
    const reportContent = document.getElementById('forecastReportContent');
    reportContent.innerHTML += deviationSection;
    
    // Scroll to deviation section
    setTimeout(() => {
        reportContent.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// Show Tool Output
function showToolOutput(agentName, toolName) {
    let output = '';
    
    // Check if this is a detection agent tool during deviation
    if (agentName === 'detection' && deviationDetected) {
        if (toolName === 'vessel') {
            output = `
                <h4><i class="fas fa-satellite"></i> Vessel Data Output</h4>
                <p><strong>Real-time Vessel Tracking Data</strong></p>
                <p style="color: #fbbf24;"><em>Data captured during deviation event</em></p>
                <hr>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6; margin-bottom: 1rem;">Vessel Identification</h5>
                    <table style="width: 100%; color: #cbd5e1;">
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Vessel Name:</td><td style="padding: 0.5rem; font-weight: 600;">MV Atlantic Pioneer</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">MMSI:</td><td style="padding: 0.5rem; font-weight: 600;">123456789</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">IMO Number:</td><td style="padding: 0.5rem; font-weight: 600;">IMO 9876543</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Flag:</td><td style="padding: 0.5rem; font-weight: 600;">United States</td></tr>
                    </table>
                </div>
                <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #ef4444; margin-bottom: 1rem;">Position Data (During Deviation)</h5>
                    <table style="width: 100%; color: #cbd5e1;">
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Current Position:</td><td style="padding: 0.5rem; font-weight: 600; color: #fbbf24;">43.5°N, 55.3°W</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Expected Position:</td><td style="padding: 0.5rem; font-weight: 600; color: #10b981;">41.0°N, 54.5°W</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Deviation Distance:</td><td style="padding: 0.5rem; font-weight: 600; color: #ef4444;">~275 nautical miles</td></tr>
                    </table>
                </div>
            `;
        } else if (toolName === 'crew') {
            output = `
                <h4><i class="fas fa-file-alt"></i> Crew Reports</h4>
                <p><strong>Bridge Watch Reports & Communications</strong></p>
                <hr>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6;">Bridge Log Entry - Oct 23, 2025 08:30 UTC</h5>
                    <p style="color: #cbd5e1; margin: 0.5rem 0;">
                        <strong>Officer of Watch:</strong> Chief Mate J. Anderson<br>
                        <strong>Weather Observations:</strong> Deteriorating conditions ahead. Barometer falling rapidly.<br>
                        <strong>Decision:</strong> Course alteration initiated to avoid developing storm system.
                    </p>
                </div>
            `;
        }
    }
    
    // Check if this is analysis agent tool during root cause analysis
    if (agentName === 'analysis') {
        if (toolName === 'weather') {
            output = `
                <h4><i class="fas fa-cloud"></i> Live Weather Tool</h4>
                <p><strong>Current Weather Conditions at Vessel Location</strong></p>
                <hr>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6;">Storm System Analysis</h5>
                    <p style="color: #cbd5e1;">
                        Low pressure system intensifying at 44°N, 52°W<br>
                        Wind: NW 35-40 knots, gusting to 50<br>
                        Wave Height: 5-6 meters<br>
                        Barometric Pressure: 988 mb and falling
                    </p>
                </div>
            `;
        } else if (toolName === 'news') {
            output = `
                <h4><i class="fas fa-newspaper"></i> News Analyzer Agent</h4>
                <p><strong>Maritime News Related to Deviation</strong></p>
                <hr>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6;">Weather Alert - Oct 23, 2025</h5>
                    <p style="color: #cbd5e1;">
                        "Atlantic storm system strengthening unexpectedly. Multiple vessels 
                        reported course deviations to avoid severe weather. Coast Guard 
                        advisory in effect for North Atlantic corridor."
                    </p>
                </div>
            `;
        }
    }
    
    // Check if this is port monitor agent tool
    if (agentName === 'portmonitor') {
        if (toolName === 'marine') {
            output = `
                <h4><i class="fas fa-water"></i> Marine Traffic Tool</h4>
                <p><strong>Porto Port - Real-time Traffic Analysis</strong></p>
                <hr>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6; margin-bottom: 1rem;">Current Port Status</h5>
                    <table style="width: 100%; color: #cbd5e1;">
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Vessels at Berth:</td><td style="padding: 0.5rem; font-weight: 600;">12</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Vessels Waiting:</td><td style="padding: 0.5rem; font-weight: 600;">2</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Average Wait Time:</td><td style="padding: 0.5rem; font-weight: 600;">45 minutes</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Traffic Density:</td><td style="padding: 0.5rem; font-weight: 600; color: #10b981;">LOW</td></tr>
                    </table>
                </div>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6;">Approaching Vessels (Next 6 hours)</h5>
                    <ul style="color: #cbd5e1;">
                        <li>MV Atlantic Pioneer (ETA: 2 hours) - Container Ship</li>
                        <li>MT Ocean Spirit (ETA: 4 hours) - Tanker</li>
                        <li>MV Nordic Express (ETA: 5.5 hours) - RoRo Vessel</li>
                    </ul>
                </div>
            `;
        } else if (toolName === 'port') {
            output = `
                <h4><i class="fas fa-clipboard-check"></i> Port Status Tool</h4>
                <p><strong>Porto Port - Operational Status</strong></p>
                <hr>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6; margin-bottom: 1rem;">Berth Availability</h5>
                    <table style="width: 100%; color: #cbd5e1;">
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Berth B-7:</td><td style="padding: 0.5rem; font-weight: 600; color: #10b981;">AVAILABLE</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Berth B-8:</td><td style="padding: 0.5rem; font-weight: 600; color: #10b981;">AVAILABLE</td></tr>
                        <tr><td style="padding: 0.5rem; color: #94a3b8;">Berth B-9:</td><td style="padding: 0.5rem; font-weight: 600; color: #fbbf24;">OCCUPIED</td></tr>
                    </table>
                </div>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #3b82f6;">Port Operations</h5>
                    <p style="color: #cbd5e1;">
                        <strong>Weather Conditions:</strong> Clear, Wind: 8 knots SW<br>
                        <strong>Tidal Status:</strong> High tide in 1.5 hours<br>
                        <strong>Pilot Service:</strong> Available<br>
                        <strong>Tug Assistance:</strong> 2 tugs available<br>
                        <strong>Crane Operations:</strong> All 4 cranes operational
                    </p>
                </div>
            `;
        }
    }
    
    // Original tool outputs for forecast agent
    if (!output) {
        const toolOutputs = {
            weather: `
                <h4>Weather Forecast Tool Output</h4>
                <p><strong>Analysis Period:</strong> Oct 22 - Nov 3, 2025</p>
                <hr>
                <h5>Route 1 (Northern):</h5>
                <ul>
                    <li>Oct 23: Wind NW 25-30 knots, waves 3-4m</li>
                    <li>Oct 24-26: Storm system approaching, winds 35-45 knots</li>
                    <li>Oct 27-29: Improving conditions, winds 15-20 knots</li>
                </ul>
                <h5>Route 2 (Mid-Atlantic):</h5>
                <ul>
                    <li>Oct 23-25: Moderate winds 15-20 knots, waves 1-2m</li>
                    <li>Oct 26-28: Light winds 10-15 knots, calm seas</li>
                </ul>
            `,
            marine: `
                <h4>Marine Traffic Tool Output</h4>
                <p><strong>Real-time Traffic Analysis</strong></p>
                <hr>
                <h5>Current Vessel Density:</h5>
                <ul>
                    <li>Route 1: 12 vessels within 50nm radius</li>
                    <li>Route 2: 28 vessels within 50nm radius</li>
                    <li>Route 3: 45 vessels within 50nm radius</li>
                </ul>
            `,
            news: `
                <h4>News Analyzer Output</h4>
                <p><strong>Maritime News Digest - Atlantic Region</strong></p>
                <hr>
                <h5>Recent Developments:</h5>
                <ul>
                    <li><strong>Oct 21:</strong> Porto port completes terminal expansion</li>
                    <li><strong>Oct 20:</strong> Atlantic storm "Helena" weakening</li>
                </ul>
            `
        };
        output = toolOutputs[toolName] || '<p>No data available for this tool.</p>';
    }
    
    document.getElementById('modalTitle').textContent = `${toolName.charAt(0).toUpperCase() + toolName.slice(1)} Tool Output`;
    document.getElementById('modalBody').innerHTML = output;
    document.getElementById('toolModal').classList.add('active');
}

// Close Modal
function closeModal() {
    document.getElementById('toolModal').classList.remove('active');
}

// Select Route
function selectRoute(routeNum) {
    currentRoute = routeNum;
    appendLog(`[${new Date().toISOString()}] User selected Route ${routeNum}`);
    
    // Highlight selected route on map
    routeLayers.forEach((layer, index) => {
        if (index == routeNum - 1) {
            layer.setStyle({ opacity: 1, weight: 5 });
        } else {
            layer.setStyle({ opacity: 0.3, weight: 2 });
        }
    });
    
    // Replace route selection content with Start Journey button
    const routeSelectionDiv = document.getElementById('routeSelection');
    const routeName = routeNum == 1 ? 'Northern Atlantic' : routeNum == 2 ? 'Mid-Atlantic' : 'Southern Atlantic';
    
    routeSelectionDiv.innerHTML = `
        <div style="text-align: center; padding: 3rem;">
            <h2 style="margin-bottom: 2rem; color: #10b981;">
                <i class="fas fa-check-circle"></i> Route ${routeNum} Selected
            </h2>
            <p style="color: #94a3b8; margin-bottom: 2rem; font-size: 1.1rem;">
                ${routeName} Route - Ready to begin journey
            </p>
            <button id="startJourneyBtn" class="btn-start-journey">
                <i class="fas fa-ship"></i>
                Start Journey on ${routeName} Route
            </button>
        </div>
    `;
    
    // Add event listener to new button
    document.getElementById('startJourneyBtn').addEventListener('click', startJourney);
}

// Start Journey
function startJourney() {
    if (journeyInProgress) return;
    
    journeyInProgress = true;
    journeyStartDate = new Date('2025-10-22T14:35:00');
    currentProgress = 0;
    
    // Scroll to Journey Details
    document.querySelector('.journey-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Show Detection Agent notification
    showNotification('Detection Agent Active', 'Vessel tracking and monitoring initiated', 'info');
    
    // Activate Detection Agent
    const detectionStatus = document.getElementById('detectionStatus');
    if (detectionStatus) {
        detectionStatus.textContent = 'Running';
        detectionStatus.classList.add('running');
    }
    
    appendLog(`[${new Date().toISOString()}] Journey started on Route ${currentRoute}`);
    appendLog(`[${new Date().toISOString()}] Detection Agent: Initiating real-time vessel monitoring...`);
    
    // Get route coordinates for Route 2 (Mid-Atlantic)
    const boston = [42.3601, -71.0589];
    const waypoint1 = [41, -48];
    const waypoint2 = [41, -25];
    const porto = [41.1579, -8.6291];
    
    const routeCoordinates = [boston, waypoint1, waypoint2, porto];
    
    // Start journey animation
    let step = 0;
    const totalSteps = 200;
    const intervalTime = 100;
    
    journeyInterval = setInterval(() => {
        if (journeyPaused) return;
        
        step++;
        
        if (deviationDetected) {
            return;
        }
        
        currentProgress = (step / totalSteps) * 100;
        
        // Update progress bar
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${currentProgress}%`;
        }
        
        // Update vessel location text
        let currentSection = 'A';
        let sectionPercent = currentProgress;
        
        if (currentProgress < 33.33) {
            currentSection = 'A';
            sectionPercent = (currentProgress / 33.33) * 100;
        } else if (currentProgress < 66.66) {
            currentSection = 'B';
            sectionPercent = ((currentProgress - 33.33) / 33.33) * 100;
        } else {
            currentSection = 'C';
            sectionPercent = ((currentProgress - 66.66) / 33.33) * 100;
        }
        
        document.getElementById('vesselLocation').textContent = 
            `Current Section: ${currentSection} (${Math.round(sectionPercent)}% Complete)`;
        
        // Calculate interpolated position
        const segmentIndex = Math.floor((step / totalSteps) * (routeCoordinates.length - 1));
        const segmentProgress = ((step / totalSteps) * (routeCoordinates.length - 1)) - segmentIndex;
        
        let lat = boston[0];
        let lng = boston[1];
        
        if (segmentIndex < routeCoordinates.length - 1) {
            const start = routeCoordinates[segmentIndex];
            const end = routeCoordinates[segmentIndex + 1];
            
            lat = start[0] + (end[0] - start[0]) * segmentProgress;
            lng = start[1] + (end[1] - start[1]) * segmentProgress;
            
            // Update vessel marker position
            if (vesselMarker) {
                vesselMarker.setLatLng([lat, lng]);
            }
        }
        
        // Update date progressively
        if (!deviationDetected) {
            const daysElapsed = (step / totalSteps) * 12;
            const currentDate = new Date(journeyStartDate);
            currentDate.setDate(currentDate.getDate() + Math.floor(daysElapsed));
            currentDate.setHours(currentDate.getHours() + (daysElapsed % 1) * 24);
            
            document.getElementById('currentDate').textContent = currentDate.toLocaleDateString('en-US', { 
                weekday: 'short', 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        }
        
        // Check for deviation at 30% of first segment
        if (segmentIndex === 0 && segmentProgress >= 0.3 && !deviationDetected) {
            pausedStep = step;
            detectDeviation(lat, lng, segmentProgress);
        }
        
        // Check if approaching destination (95% progress)
        if (currentProgress >= 95 && !journeyPaused) {
            pausedStep = step;
            journeyPaused = true;
            activatePortMonitor();
        }
        
        // Complete journey
        if (step >= totalSteps) {
            clearInterval(journeyInterval);
            journeyInProgress = false;
        }
    }, intervalTime);
}

// Detect Deviation
function detectDeviation(currentLat, currentLng, segmentProgress) {
    deviationDetected = true;
    
    const boston = [42.3601, -71.0589];
    const waypoint1 = [41, -48];
    
    const expectedLat = boston[0] + (waypoint1[0] - boston[0]) * 0.3;
    const expectedLng = boston[1] + (waypoint1[1] - boston[1]) * 0.3;
    
    const deviatedLat = expectedLat + 2.5;
    const deviatedLng = expectedLng - 1.8;
    
    if (vesselMarker) {
        vesselMarker.setLatLng([deviatedLat, deviatedLng]);
    }
    
    showNotification(
        'Deviation Detected',
        `Vessel significantly off designated coordinates. Current: ${deviatedLat.toFixed(4)}°N, ${Math.abs(deviatedLng).toFixed(4)}°W | Expected: ${expectedLat.toFixed(4)}°N, ${Math.abs(expectedLng).toFixed(4)}°W`,
        'warning'
    );
    
    const detectionCard = document.querySelector('[data-agent="detection"]');
    if (detectionCard) {
        const existingAlert = detectionCard.querySelector('.deviation-alert');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        const deviationInfo = document.createElement('div');
        deviationInfo.className = 'deviation-alert';
        deviationInfo.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 1rem; margin-top: 0.5rem;">
                <h5 style="color: #ef4444; margin-bottom: 0.5rem;">
                    <i class="fas fa-exclamation-triangle"></i> Deviation Detected
                </h5>
                <p style="font-size: 0.85rem; color: #fbbf24; margin-bottom: 0.5rem;">
                    Vessel significantly off designated coordinates
                </p>
                <p style="font-size: 0.8rem; color: #94a3b8; margin: 0;">
                    <strong>Current:</strong> ${deviatedLat.toFixed(4)}°N, ${Math.abs(deviatedLng).toFixed(4)}°W<br>
                    <strong>Expected:</strong> ${expectedLat.toFixed(4)}°N, ${Math.abs(expectedLng).toFixed(4)}°W<br>
                    <strong>Deviation:</strong> ${Math.abs(deviatedLat - expectedLat).toFixed(2)}° Lat, ${Math.abs(deviatedLng - expectedLng).toFixed(2)}° Lon
                </p>
            </div>
        `;
        detectionCard.appendChild(deviationInfo);
        
        const toolsDiv = detectionCard.querySelector('.agent-tools');
        if (toolsDiv) {
            toolsDiv.innerHTML = `
                <div class="tool-item" data-tool="vessel">
                    <i class="fas fa-satellite"></i>
                    <span>Vessel Data</span>
                </div>
                <div class="tool-item" data-tool="crew">
                    <i class="fas fa-file-alt"></i>
                    <span>Crew Reports</span>
                </div>
            `;
            
            toolsDiv.querySelectorAll('.tool-item').forEach(tool => {
                tool.addEventListener('click', (e) => {
                    const toolName = e.currentTarget.dataset.tool;
                    showToolOutput('detection', toolName);
                });
            });
        }
    }
    
    updateReportWithDeviation(deviatedLat, deviatedLng, expectedLat, expectedLng);
    
    setTimeout(() => {
        document.getElementById('forecastReport').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 500);
    
    appendLog(`[${new Date().toISOString()}] Detection Agent: DEVIATION DETECTED`);
    appendLog(`[${new Date().toISOString()}] Detection Agent: Current position: ${deviatedLat.toFixed(4)}°N, ${Math.abs(deviatedLng).toFixed(4)}°W`);
    appendLog(`[${new Date().toISOString()}] Detection Agent: Expected position: ${expectedLat.toFixed(4)}°N, ${Math.abs(expectedLng).toFixed(4)}°W`);
    appendLog(`[${new Date().toISOString()}] Detection Agent: Alerting Analysis Agent...`);
    
    setTimeout(() => {
        showRootCauseOptions();
    }, 2000);
}

// Show Root Cause Analysis Options
function showRootCauseOptions() {
    const existingOptions = document.getElementById('rootCauseOptions');
    if (existingOptions) {
        existingOptions.remove();
    }
    
    const optionsDiv = document.createElement('div');
    optionsDiv.id = 'rootCauseOptions';
    optionsDiv.className = 'root-cause-options';
    optionsDiv.innerHTML = `
        <div style="background: rgba(30, 41, 59, 0.95); border: 2px solid #fbbf24; border-radius: 12px; padding: 2rem; margin: 1rem; text-align: center; animation: slideUp 0.5s ease;">
            <h3 style="color: #fbbf24; margin-bottom: 1rem;">
                <i class="fas fa-search"></i> Deviation Response Required
            </h3>
            <p style="color: #cbd5e1; margin-bottom: 2rem;">
                A significant course deviation has been detected. Would you like to initiate root cause analysis?
            </p>
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <button id="startRootCauseBtn" class="btn-root-cause">
                    <i class="fas fa-microscope"></i>
                    Start Root Cause Analysis
                </button>
                <button id="continueJourneyBtn" class="btn-continue">
                    <i class="fas fa-forward"></i>
                    Continue Monitoring
                </button>
            </div>
        </div>
    `;
    
    const logsSection = document.getElementById('agentLogs');
    logsSection.parentNode.insertBefore(optionsDiv, logsSection);
    
    optionsDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    document.getElementById('startRootCauseBtn').addEventListener('click', startRootCauseAnalysis);
    document.getElementById('continueJourneyBtn').addEventListener('click', continueJourney);
}

// Start Root Cause Analysis
function startRootCauseAnalysis() {
    appendLog(`[${new Date().toISOString()}] User initiated Root Cause Analysis`);
    appendLog(`[${new Date().toISOString()}] Analysis Agent: Starting comprehensive deviation analysis...`);
    
    const analysisStatus = document.getElementById('analysisStatus');
    if (analysisStatus) {
        analysisStatus.textContent = 'Running';
        analysisStatus.classList.add('running');
    }
    
    const optionsDiv = document.getElementById('rootCauseOptions');
    if (optionsDiv) {
        optionsDiv.remove();
    }
    
    showNotification('Root Cause Analysis Started', 'Analysis Agent investigating deviation causes', 'info');
    
    const analysisCard = document.querySelector('[data-agent="analysis"]');
    if (analysisCard) {
        const toolsDiv = analysisCard.querySelector('.agent-tools');
        if (toolsDiv) {
            toolsDiv.querySelectorAll('.tool-item').forEach(tool => {
                tool.addEventListener('click', (e) => {
                    const toolName = e.currentTarget.dataset.tool;
                    showToolOutput('analysis', toolName);
                });
            });
        }
    }
    
    appendLog(`[${new Date().toISOString()}] Analysis Agent: Analyzing vessel data...`);
    
    setTimeout(() => {
        appendLog(`[${new Date().toISOString()}] Analysis Agent: Reviewing crew reports...`);
    }, 2000);
    
    setTimeout(() => {
        appendLog(`[${new Date().toISOString()}] Analysis Agent: Checking live weather conditions...`);
    }, 4000);
    
    setTimeout(() => {
        appendLog(`[${new Date().toISOString()}] Analysis Agent: Scanning maritime news sources...`);
    }, 6000);
    
    setTimeout(() => {
        showAnalysisResults();
    }, 8000);
}

// Show Analysis Results
function showAnalysisResults() {
    const analysisStatus = document.getElementById('analysisStatus');
    if (analysisStatus) {
        analysisStatus.textContent = 'Idle';
        analysisStatus.classList.remove('running');
    }
    
    appendLog(`[${new Date().toISOString()}] Analysis Agent: Root cause analysis completed`);
    appendLog(`[${new Date().toISOString()}] Analysis Agent: Weather avoidance maneuver identified as primary cause`);
    
    // Add analysis report to forecast report
    const analysisReport = `
        <div style="margin: 2rem 0; padding: 1.5rem; background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; border-radius: 8px;">
            <h4 style="color: #3b82f6; margin-bottom: 1rem;">
                <i class="fas fa-microscope"></i> Root Cause Analysis Report
            </h4>
            <h5 style="color: #10b981; margin-bottom: 1rem;">Executive Summary</h5>
            <p style="color: #cbd5e1; margin-bottom: 1rem;">
                The deviation from Route 2 (Mid-Atlantic) was a <strong>justified weather avoidance maneuver</strong>. 
                The vessel's master made a prudent decision to alter course to avoid a rapidly intensifying storm system.
            </p>
            
            <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Root Cause: Weather Avoidance</h5>
            <ul style="color: #cbd5e1; margin-bottom: 1rem;">
                <li>Storm system intensified faster than originally forecasted</li>
                <li>Barometric pressure dropped to 988 mb (below prediction of 995 mb)</li>
                <li>Wind speeds reached 40 knots with gusts to 50 knots</li>
                <li>Wave heights increased to 5-6 meters</li>
            </ul>
            
            <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Contributing Factors</h5>
            <ul style="color: #cbd5e1; margin-bottom: 1rem;">
                <li>Bridge team identified deteriorating conditions through onboard monitoring</li>
                <li>Crew reports confirmed worsening weather ahead</li>
                <li>Maritime news sources reported multiple vessels altering course</li>
                <li>Coast Guard issued weather advisory for the area</li>
            </ul>
            
            <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Decision Analysis</h5>
            <p style="color: #cbd5e1; margin-bottom: 1rem;">
                The master's decision to deviate was appropriate and in accordance with good seamanship. 
                Safety of vessel and crew takes precedence over schedule adherence. The alternative 
                route adds approximately 50 nautical miles but ensures safe passage.
            </p>
            
            <h5 style="color: #10b981; margin-bottom: 0.5rem;">Conclusion</h5>
            <p style="color: #cbd5e1;">
                <strong>Deviation Status: JUSTIFIED</strong><br>
                The vessel should continue on the adjusted course. No corrective action required. 
                Expected arrival delay: 4-6 hours. Recommend continuing journey and monitoring weather conditions.
            </p>
            
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 1rem; font-style: italic;">
                Analysis completed by Analysis Agent at ${new Date().toLocaleTimeString('en-US')} UTC
            </p>
        </div>
    `;
    
    const reportContent = document.getElementById('forecastReportContent');
    reportContent.innerHTML += analysisReport;
    
    setTimeout(() => {
        reportContent.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
    
    showNotification('Analysis Complete', 'Root cause identified: Weather avoidance maneuver. Deviation was justified.', 'success');
    
    // Show route decision options
    setTimeout(() => {
        showRouteDecisionOptions();
    }, 2000);
}

// Show Route Decision Options - NEW FUNCTION
function showRouteDecisionOptions() {
    const existingOptions = document.getElementById('routeDecisionOptions');
    if (existingOptions) {
        existingOptions.remove();
    }
    
    const optionsDiv = document.createElement('div');
    optionsDiv.id = 'routeDecisionOptions';
    optionsDiv.className = 'route-decision-options';
    optionsDiv.innerHTML = `
        <div style="background: rgba(30, 41, 59, 0.95); border: 2px solid #3b82f6; border-radius: 12px; padding: 2rem; margin: 1rem; text-align: center; animation: slideUp 0.5s ease;">
            <h3 style="color: #3b82f6; margin-bottom: 1rem;">
                <i class="fas fa-route"></i> Route Decision Required
            </h3>
            <p style="color: #cbd5e1; margin-bottom: 1rem;">
                The deviation was justified due to severe weather conditions. The Analysis Agent recommends continuing on the adjusted course.
            </p>
            <p style="color: #10b981; margin-bottom: 2rem; font-weight: 600;">
                Would you like to continue on the same route or change to an alternative route?
            </p>
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <button id="continueRouteBtn" class="btn-root-cause">
                    <i class="fas fa-check"></i>
                    Continue on Same Route
                </button>
                <button id="changeRouteBtn" class="btn-continue">
                    <i class="fas fa-exchange-alt"></i>
                    Change Route
                </button>
            </div>
        </div>
    `;
    
    const reportSection = document.getElementById('forecastReport');
    reportSection.parentNode.insertBefore(optionsDiv, reportSection.nextSibling);
    
    optionsDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    document.getElementById('continueRouteBtn').addEventListener('click', continueOnSameRoute);
    document.getElementById('changeRouteBtn').addEventListener('click', () => {
        showNotification('Route Change', 'Please contact Resolution Agent for alternative routes', 'info');
    });
}

// Continue on Same Route - NEW FUNCTION
function continueOnSameRoute() {
    appendLog(`[${new Date().toISOString()}] User decided to continue on same route`);
    appendLog(`[${new Date().toISOString()}] Detection Agent: Resuming vessel monitoring...`);
    
    const optionsDiv = document.getElementById('routeDecisionOptions');
    if (optionsDiv) {
        optionsDiv.remove();
    }
    
    showNotification('Journey Resumed', 'Vessel continuing on adjusted route toward Porto', 'success');
    
    // Resume journey
    deviationDetected = false;
    resumeJourney();
}

// Resume Journey - NEW FUNCTION
function resumeJourney() {
    const boston = [42.3601, -71.0589];
    const waypoint1 = [41, -48];
    const waypoint2 = [41, -25];
    const porto = [41.1579, -8.6291];
    
    const routeCoordinates = [boston, waypoint1, waypoint2, porto];
    const totalSteps = 200;
    const intervalTime = 100;
    
    let step = pausedStep;
    
    journeyInterval = setInterval(() => {
        if (journeyPaused) return;
        
        step++;
        currentProgress = (step / totalSteps) * 100;
        
        // Update progress bar
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${currentProgress}%`;
        }
        
        // Update vessel location
        let currentSection = 'A';
        let sectionPercent = currentProgress;
        
        if (currentProgress < 33.33) {
            currentSection = 'A';
            sectionPercent = (currentProgress / 33.33) * 100;
        } else if (currentProgress < 66.66) {
            currentSection = 'B';
            sectionPercent = ((currentProgress - 33.33) / 33.33) * 100;
        } else {
            currentSection = 'C';
            sectionPercent = ((currentProgress - 66.66) / 33.33) * 100;
        }
        
        document.getElementById('vesselLocation').textContent = 
            `Current Section: ${currentSection} (${Math.round(sectionPercent)}% Complete)`;
        
        // Calculate interpolated position
        const segmentIndex = Math.floor((step / totalSteps) * (routeCoordinates.length - 1));
        const segmentProgress = ((step / totalSteps) * (routeCoordinates.length - 1)) - segmentIndex;
        
        if (segmentIndex < routeCoordinates.length - 1) {
            const start = routeCoordinates[segmentIndex];
            const end = routeCoordinates[segmentIndex + 1];
            
            const lat = start[0] + (end[0] - start[0]) * segmentProgress;
            const lng = start[1] + (end[1] - start[1]) * segmentProgress;
            
            if (vesselMarker) {
                vesselMarker.setLatLng([lat, lng]);
            }
        }
        
        // Update date
        const daysElapsed = (step / totalSteps) * 12;
        const currentDate = new Date(journeyStartDate);
        currentDate.setDate(currentDate.getDate() + Math.floor(daysElapsed));
        currentDate.setHours(currentDate.getHours() + (daysElapsed % 1) * 24);
        
        document.getElementById('currentDate').textContent = currentDate.toLocaleDateString('en-US', { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
        
        // Check if approaching destination (95% progress)
        if (currentProgress >= 95 && !journeyPaused) {
            pausedStep = step;
            journeyPaused = true;
            activatePortMonitor();
        }
        
        // Complete journey
        if (step >= totalSteps) {
            clearInterval(journeyInterval);
            journeyInProgress = false;
        }
    }, intervalTime);
}

// Activate Port Monitor - NEW FUNCTION
function activatePortMonitor() {
    appendLog(`[${new Date().toISOString()}] Detection Agent: Vessel approaching destination`);
    appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Activating for Porto port assessment...`);
    
    // Activate Port Monitor Agent
    const portMonitorStatus = document.getElementById('portmonitorStatus');
    if (portMonitorStatus) {
        portMonitorStatus.textContent = 'Running';
        portMonitorStatus.classList.add('running');
    }
    
    showNotification('Approaching Destination', 'Port Monitor Agent activated for Porto port assessment', 'info');
    
    // Scroll to Port Monitor Agent card
    const portMonitorCard = document.querySelector('[data-agent="portmonitor"]');
    if (portMonitorCard) {
        setTimeout(() => {
            portMonitorCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 500);
        
        // Make tools clickable
        const toolsDiv = portMonitorCard.querySelector('.agent-tools');
        if (toolsDiv) {
            toolsDiv.querySelectorAll('.tool-item').forEach(tool => {
                tool.style.cursor = 'pointer';
                tool.addEventListener('click', (e) => {
                    const toolName = e.currentTarget.dataset.tool;
                    showToolOutput('portmonitor', toolName);
                });
            });
        }
    }
    
    // Generate port assessment after 3 seconds
    setTimeout(() => {
        appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Analyzing marine traffic at Porto...`);
    }, 1000);
    
    setTimeout(() => {
        appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Checking berth availability...`);
    }, 2000);
    
    setTimeout(() => {
        appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Assessment complete`);
        showPortAssessmentReport();
    }, 5000);
}

// Show Port Assessment Report - NEW FUNCTION
function showPortAssessmentReport() {
    const portMonitorStatus = document.getElementById('portmonitorStatus');
    if (portMonitorStatus) {
        portMonitorStatus.textContent = 'Idle';
        portMonitorStatus.classList.remove('running');
    }
    
    const portReport = `
        <div style="margin: 2rem 0; padding: 1.5rem; background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; border-radius: 8px;">
            <h4 style="color: #10b981; margin-bottom: 1rem;">
                <i class="fas fa-anchor"></i> Port Assessment Report - Porto
            </h4>
            
            <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Port Status Summary</h5>
            <p style="color: #cbd5e1; margin-bottom: 1rem;">
                Porto port is operating normally with favorable conditions for docking. 
                The port has completed its terminal expansion, providing excellent facilities for container operations.
            </p>
            
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Berth Availability Analysis</h5>
                <table style="width: 100%; color: #cbd5e1;">
                    <tr>
                        <td style="padding: 0.5rem; color: #94a3b8;"><strong>Berth B-7:</strong></td>
                        <td style="padding: 0.5rem; color: #10b981; font-weight: 600;">AVAILABLE</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; color: #94a3b8;"><strong>Berth B-8:</strong></td>
                        <td style="padding: 0.5rem; color: #10b981; font-weight: 600;">AVAILABLE</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; color: #94a3b8;"><strong>Recommended:</strong></td>
                        <td style="padding: 0.5rem; color: #10b981; font-weight: 600;">BERTH B-7</td>
                    </tr>
                </table>
            </div>
            
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Traffic Conditions</h5>
                <ul style="color: #cbd5e1;">
                    <li><strong>Current vessels at berth:</strong> 12</li>
                    <li><strong>Vessels waiting:</strong> 2 (average wait: 45 minutes)</li>
                    <li><strong>Traffic density:</strong> LOW</li>
                    <li><strong>Approaching vessels (next 6 hours):</strong> 3</li>
                </ul>
            </div>
            
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Environmental Conditions</h5>
                <ul style="color: #cbd5e1;">
                    <li><strong>Weather:</strong> Clear skies, Wind 8 knots SW</li>
                    <li><strong>Tidal status:</strong> High tide in 1.5 hours (optimal for docking)</li>
                    <li><strong>Visibility:</strong> Excellent (>10 nm)</li>
                    <li><strong>Sea state:</strong> Calm</li>
                </ul>
            </div>
            
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h5 style="color: #3b82f6; margin-bottom: 0.5rem;">Port Services Status</h5>
                <ul style="color: #cbd5e1;">
                    <li><strong>Pilot service:</strong> Available</li>
                    <li><strong>Tug assistance:</strong> 2 tugs available</li>
                    <li><strong>Crane operations:</strong> All 4 cranes operational</li>
                    <li><strong>Customs clearance:</strong> Fast-track available</li>
                </ul>
            </div>
            
            <h5 style="color: #10b981; margin-top: 1.5rem; margin-bottom: 0.5rem;">Docking Recommendation</h5>
            <p style="color: #cbd5e1; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 6px;">
                <strong>PROCEED TO DOCK AT BERTH B-7</strong><br>
                All conditions are favorable. Recommended docking time: Within 2 hours (aligned with high tide).<br>
                Expected berth occupancy: 18-24 hours for cargo operations.
            </p>
            
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 1rem; font-style: italic;">
                Assessment completed by Port Monitor Agent at ${new Date().toLocaleTimeString('en-US')} UTC
            </p>
        </div>
    `;
    
    const reportContent = document.getElementById('forecastReportContent');
    reportContent.innerHTML += portReport;
    
    setTimeout(() => {
        reportContent.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
    
    showNotification('Port Assessment Complete', 'Berth B-7 available. Favorable conditions for docking.', 'success');
    
    // Show docking decision options
    setTimeout(() => {
        showDockingDecisionOptions();
    }, 2000);
}

// Show Docking Decision Options - NEW FUNCTION
function showDockingDecisionOptions() {
    const existingOptions = document.getElementById('dockingDecisionOptions');
    if (existingOptions) {
        existingOptions.remove();
    }
    
    const optionsDiv = document.createElement('div');
    optionsDiv.id = 'dockingDecisionOptions';
    optionsDiv.className = 'docking-decision-options';
    optionsDiv.innerHTML = `
        <div style="background: rgba(30, 41, 59, 0.95); border: 2px solid #10b981; border-radius: 12px; padding: 2rem; margin: 1rem; text-align: center; animation: slideUp 0.5s ease;">
            <h3 style="color: #10b981; margin-bottom: 1rem;">
                <i class="fas fa-anchor"></i> Docking Decision Required
            </h3>
            <p style="color: #cbd5e1; margin-bottom: 1rem;">
                Port Monitor Agent has completed the assessment. Porto port is ready to receive MV Atlantic Pioneer.
            </p>
            <div style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 8px; margin: 1.5rem 0;">
                <p style="color: #10b981; font-weight: 600; margin: 0;">
                    <i class="fas fa-check-circle"></i> Berth B-7 Available
                </p>
                <p style="color: #cbd5e1; font-size: 0.9rem; margin: 0.5rem 0 0 0;">
                    All conditions favorable • High tide in 1.5 hours • Services ready
                </p>
            </div>
            <p style="color: #cbd5e1; margin-bottom: 2rem;">
                Would you like to proceed with docking at Berth B-7?
            </p>
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <button id="acceptDockingBtn" class="btn-root-cause">
                    <i class="fas fa-check"></i>
                    Accept & Proceed to Dock
                </button>
                <button id="delayDockingBtn" class="btn-continue">
                    <i class="fas fa-clock"></i>
                    Delay Docking
                </button>
            </div>
        </div>
    `;
    
    const reportSection = document.getElementById('forecastReport');
    reportSection.parentNode.insertBefore(optionsDiv, reportSection.nextSibling);
    
    optionsDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    document.getElementById('acceptDockingBtn').addEventListener('click', acceptDocking);
    document.getElementById('delayDockingBtn').addEventListener('click', () => {
        showNotification('Docking Delayed', 'Vessel will maintain holding position', 'info');
    });
}

// Accept Docking - NEW FUNCTION
function acceptDocking() {
    appendLog(`[${new Date().toISOString()}] User accepted docking recommendation`);
    appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Coordinating with port authority...`);
    appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Pilot service dispatched`);
    appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Tug assistance confirmed`);
    
    const optionsDiv = document.getElementById('dockingDecisionOptions');
    if (optionsDiv) {
        optionsDiv.remove();
    }
    
    showNotification('Docking Initiated', 'Vessel proceeding to Berth B-7', 'success');
    
    // Complete the journey
    journeyPaused = false;
    
    setTimeout(() => {
        completeJourney();
    }, 3000);
}

// Complete Journey - NEW FUNCTION
function completeJourney() {
    // Stop the journey
    if (journeyInterval) {
        clearInterval(journeyInterval);
    }
    
    journeyInProgress = false;
    
    // Update progress to 100%
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = '100%';
    }
    
    document.getElementById('vesselLocation').textContent = 'Docked at Porto - Berth B-7';
    
    // Move vessel to Porto position
    const porto = [41.1579, -8.6291];
    if (vesselMarker) {
        vesselMarker.setLatLng(porto);
    }
    
    // Deactivate agents
    const detectionStatus = document.getElementById('detectionStatus');
    if (detectionStatus) {
        detectionStatus.textContent = 'Idle';
        detectionStatus.classList.remove('running');
    }
    
    const portMonitorStatus = document.getElementById('portmonitorStatus');
    if (portMonitorStatus) {
        portMonitorStatus.textContent = 'Idle';
        portMonitorStatus.classList.remove('running');
    }
    
    appendLog(`[${new Date().toISOString()}] Port Monitor Agent: Vessel secured at Berth B-7`);
    appendLog(`[${new Date().toISOString()}] Detection Agent: Journey monitoring completed`);
    appendLog(`[${new Date().toISOString()}] System: Shipment CARGO-2025-11-BST-PRT delivered successfully`);
    
    // Show completion notification
    showCompletionNotification();
}

// Show Completion Notification - NEW FUNCTION
function showCompletionNotification() {
    const notification = document.createElement('div');
    notification.className = 'completion-notification';
    notification.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: rgba(30, 41, 59, 0.98); border: 3px solid #10b981; border-radius: 16px; 
                    padding: 3rem; text-align: center; z-index: 10001; min-width: 500px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5); animation: slideUp 0.5s ease;">
            <div style="font-size: 4rem; color: #10b981; margin-bottom: 1rem;">
                <i class="fas fa-check-circle"></i>
            </div>
            <h2 style="color: #10b981; margin-bottom: 1rem; font-size: 2rem;">
                Journey Completed Successfully!
            </h2>
            <div style="background: rgba(16, 185, 129, 0.1); padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0;">
                <p style="color: #cbd5e1; font-size: 1.1rem; margin-bottom: 0.5rem;">
                    <strong>MV Atlantic Pioneer</strong>
                </p>
                <p style="color: #94a3b8; margin: 0;">
                    Successfully docked at Porto Port, Berth B-7
                </p>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0; text-align: left;">
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px;">
                    <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.25rem;">Shipment ID</p>
                    <p style="color: #cbd5e1; font-weight: 600; margin: 0;">CARGO-2025-11-BST-PRT</p>
                </div>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px;">
                    <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.25rem;">Journey Status</p>
                    <p style="color: #10b981; font-weight: 600; margin: 0;">COMPLETED</p>
                </div>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px;">
                    <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.25rem;">Route</p>
                    <p style="color: #cbd5e1; font-weight: 600; margin: 0;">Boston → Porto</p>
                </div>
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px;">
                    <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.25rem;">Arrival Time</p>
                    <p style="color: #cbd5e1; font-weight: 600; margin: 0;">${new Date().toLocaleTimeString()}</p>
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 2rem;">
                All AI agents have completed their tasks. Cargo operations will begin shortly.
            </p>
            <button onclick="closeCompletionNotification()" class="btn-root-cause">
                <i class="fas fa-times"></i>
                Close
            </button>
        </div>
        <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                    background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(5px); z-index: 10000;"></div>
    `;
    
    document.body.appendChild(notification);
    
    // Show final notification
    setTimeout(() => {
        showNotification('Journey Complete', 'MV Atlantic Pioneer successfully docked at Porto Port', 'success');
    }, 500);
}

// Close Completion Notification - NEW FUNCTION
function closeCompletionNotification() {
    const notification = document.querySelector('.completion-notification');
    if (notification) {
        notification.remove();
    }
}

// Continue Journey (from deviation)
function continueJourney() {
    appendLog(`[${new Date().toISOString()}] User chose to continue monitoring`);
    
    const optionsDiv = document.getElementById('rootCauseOptions');
    if (optionsDiv) {
        optionsDiv.remove();
    }
    
    showNotification('Monitoring Continued', 'Detection Agent continues tracking vessel position', 'info');
}

// Show Notification
function showNotification(title, message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-header">
                <span class="notification-title">
                    <i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : type === 'info' ? 'info-circle' : 'check-circle'}"></i>
                    ${title}
                </span>
                <button class="notification-close" onclick="closeNotification(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
        </div>
    `;
    
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
}

// Close Notification
function closeNotification(button) {
    const notification = button.closest('.notification');
    notification.classList.remove('show');
    setTimeout(() => {
        notification.remove();
    }, 300);
}

// Agent Logs Management
function initializeAgentLogs() {
    appendLog('[2025-10-22 14:30:00] System: Maritime AI Orchestrator initialized');
    appendLog('[2025-10-22 14:30:01] System: Connecting to Strands Agent Framework...');
    appendLog('[2025-10-22 14:30:02] System: Loading agent configurations...');
    appendLog('[2025-10-22 14:30:03] System: 6 agents ready for deployment');
    appendLog('[2025-10-22 14:30:04] System: Waiting for forecast initialization...');
}

function appendLog(message) {
    const logsContent = document.getElementById('logsContent');
    logsContent.textContent += message + '\n';
    
    const logsContainer = document.getElementById('logsContainer');
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Utility Functions
function updateDateTime() {
    if (!journeyInProgress || deviationDetected) {
        const now = new Date();
        if (!journeyInProgress) {
            document.getElementById('currentDate').textContent = now.toLocaleDateString('en-US', { 
                weekday: 'short', 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        }
    }
    
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function showLoading(text) {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}
