"""FastAPI application for Maritime Exception Resolution System"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn

from main import MaritimeExceptionResolver
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Store active sessions (in production, use Redis or database)
active_sessions = {}

# Initialize the resolver
resolver = MaritimeExceptionResolver()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info("Maritime Exception Resolution System starting up...")
    logger.info(f"Debug mode: {settings.APP_DEBUG}")
    logger.info(f"Listening on {settings.APP_HOST}:{settings.APP_PORT}")
    
    yield
    
    # Shutdown
    logger.info("Maritime Exception Resolution System shutting down...")
    if active_sessions:
        logger.info(f"Saving {len(active_sessions)} active sessions...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Maritime Exception Resolution System",
    description="AI-powered maritime route optimization and exception handling",
    version="1.0.0",
    lifespan=lifespan
)

# Setup templates and static files
templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Pydantic models for requests/responses
class RouteAnalysisRequest(BaseModel):
    origin_port: str = Field(..., description="Origin port name")
    destination_port: str = Field(..., description="Destination port name")
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    carrier_id: str = Field(..., description="Carrier identifier")
    preferred_arrival_date: Optional[str] = Field(None, description="Preferred arrival date")
    user_preferences: Optional[Dict] = Field(default_factory=dict)

class RouteSelectionRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    selected_route_id: str = Field(..., description="Selected route ID")
    confirmation: bool = Field(..., description="User confirmation")

class JourneyStartRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    actual_departure_date: str = Field(..., description="Actual departure date")
    vessel_details: Optional[Dict] = Field(default_factory=dict)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main interface."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Maritime Exception Resolution"}
    )

@app.post("/api/analyze-route")
async def analyze_route(request: RouteAnalysisRequest):
    """Analyze routes and provide recommendations."""
    try:
        logger.info(f"Analyzing route: {request.origin_port} -> {request.destination_port}")
        
        # Perform analysis
        result = resolver.analyze_route(
            origin_port=request.origin_port,
            destination_port=request.destination_port,
            departure_date=request.departure_date,
            carrier_id=request.carrier_id,
            user_preferences=request.user_preferences
        )
        
        if result["status"] == "success":
            # Create session for this analysis
            session_id = f"session_{datetime.now().timestamp()}"
            active_sessions[session_id] = {
                "analysis": result,
                "request": request.dict(),
                "created_at": datetime.now().isoformat(),
                "status": "awaiting_selection"
            }
            
            return JSONResponse(content={
                "status": "success",
                "session_id": session_id,
                "recommendations": result["recommendations"],
                "message": "Analysis complete. Please select a route."
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error in route analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/select-route")
async def select_route(request: RouteSelectionRequest):
    """Handle user route selection."""
    try:
        # Validate session
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[request.session_id]
        
        if not request.confirmation:
            return JSONResponse(content={
                "status": "cancelled",
                "message": "Route selection cancelled by user"
            })
        
        # Update session with selection
        session["selected_route"] = request.selected_route_id
        session["status"] = "route_selected"
        session["selection_time"] = datetime.now().isoformat()
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Route {request.selected_route_id} selected successfully",
            "next_step": "Confirm departure date to start journey"
        })
        
    except Exception as e:
        logger.error(f"Error in route selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start-journey")
async def start_journey(request: JourneyStartRequest):
    """Start the journey with selected route."""
    try:
        # Validate session
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[request.session_id]
        
        if session["status"] != "route_selected":
            raise HTTPException(status_code=400, detail="No route selected")
        
        # Update session with journey start
        session["journey_started"] = True
        session["actual_departure"] = request.actual_departure_date
        session["vessel_details"] = request.vessel_details
        session["status"] = "in_progress"
        session["start_time"] = datetime.now().isoformat()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Journey started successfully",
            "session_id": request.session_id,
            "tracking_enabled": True,
            "estimated_arrival": session.get("estimated_arrival", "TBD")
        })
        
    except Exception as e:
        logger.error(f"Error starting journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/journey-status/{session_id}")
async def get_journey_status(session_id: str):
    """Get current journey status."""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        
        # Get real-time status
        if session.get("selected_route"):
            status = resolver.get_route_status(session["selected_route"])
        else:
            status = {"status": "not_started", "message": "Journey not yet started"}
        
        return JSONResponse(content={
            "status": "success",
            "session_status": session["status"],
            "journey_status": status,
            "session_data": {
                "origin": session["request"]["origin_port"],
                "destination": session["request"]["destination_port"],
                "departure_date": session["request"]["departure_date"],
                "selected_route": session.get("selected_route")
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting journey status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/active-sessions")
async def get_active_sessions():
    """Get list of active sessions (admin endpoint)."""
    return JSONResponse(content={
        "total_sessions": len(active_sessions),
        "sessions": [
            {
                "session_id": sid,
                "status": session["status"],
                "created_at": session["created_at"],
                "origin": session["request"]["origin_port"],
                "destination": session["request"]["destination_port"]
            }
            for sid, session in active_sessions.items()
        ]
    })

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return JSONResponse(content={"status": "success", "message": "Session deleted"})
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/api/ports")
async def get_available_ports():
    """Get list of available ports."""
    # Load ports from data file
    ports_file = settings.PORT_LOCATIONS_FILE
    if ports_file.exists():
        import pandas as pd
        ports_df = pd.read_csv(ports_file)
        ports = ports_df[["PORT_CITY", "PORT_CODE", "PORT_LATITUDE", "PORT_LONGITUDE"]].to_dict('records')
        return JSONResponse(content={"ports": ports})
    else:
        return JSONResponse(content={"ports": []})

@app.get("/api/carriers")
async def get_available_carriers():
    """Get list of available carriers."""
    # Load carriers from data file
    carriers_file = settings.CARRIER_SCHEDULE_FILE
    if carriers_file.exists():
        import pandas as pd
        carriers_df = pd.read_csv(carriers_file)
        carriers = carriers_df[["CARRIER_ID", "CARRIER_NAME", "SERVICE_TYPE"]].drop_duplicates().to_dict('records')
        return JSONResponse(content={"carriers": carriers})
    else:
        return JSONResponse(content={"carriers": []})

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )