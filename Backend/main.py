from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import osmnx as ox
import networkx as nx
import requests
import random
from datetime import datetime

app = FastAPI()

origins = [
    "http://localhost:5173",   
    "http://127.0.0.1:5173",
    "http://localhost:3000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RideRequest(BaseModel):
    pickup: str
    drop: str

def get_coordinates(place):
    if not place or place.strip() == "":
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "ride-simulator-project"}
    params = {"q": place, "format": "json", "limit": 1}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if len(data) == 0:
            return None, None
        return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None, None

def surge_multiplier(demand, supply):
    if supply == 0:
        return 2.0
    ratio = demand / supply
    if ratio < 1:
        return 1.0
    elif ratio < 1.5:
        return 1.2
    elif ratio < 2:
        return 1.5
    else:
        return 2.0

def calculate_fare(distance_meters, base, per_km, surge):
    distance_km = distance_meters / 1000
    base_price = base + time_increment()
    fare = base_price + (distance_km * per_km)
    return round(fare * surge, 2)

# -----------------------------
# Time Based Fare Adjustment
# -----------------------------
def time_increment():
    hour = datetime.now().hour

    if 0 <= hour < 6:         # 12AM - 6AM
        return 100
    elif 6 <= hour < 10:      # 6AM - 10AM
        return 20
    elif 10 <= hour < 15:     # 10AM - 3PM
        return 30
    elif 15 <= hour < 21:     # 3PM - 9PM
        return 0
    elif 21 <= hour <= 23:    # 9PM - 12AM
        return 30
    return 0
@app.get("/api/health")
async def health_check():    
    return {"status": "ok"}

@app.post("/api/calculate-ride")
async def calculate_ride(request: RideRequest):
    lat1, lon1 = get_coordinates(request.pickup)
    lat2, lon2 = get_coordinates(request.drop)

    if lat1 is None or lat2 is None:
        raise HTTPException(status_code=400, detail="Invalid locations. Could not geocode.")

    try:
        G = ox.graph_from_point((lat1, lon1), dist=7000, network_type='drive')
        orig_node = ox.nearest_nodes(G, lon1, lat1)
        dest_node = ox.nearest_nodes(G, lon2, lat2)

        route = nx.shortest_path(G, orig_node, dest_node, weight='length')
        distance = nx.shortest_path_length(G, orig_node, dest_node, weight='length')
        
        route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]

    except Exception as e:
        print(f"Routing error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Route could not be calculated (locations might be too far apart)."
        )

    # -----------------------------
    # Simulation Logic
    # -----------------------------
    demand = random.randint(50, 120)
    supply = random.randint(30, 100)
    surge = surge_multiplier(demand, supply)

    # -----------------------------
    # Pricing Strategies
    # -----------------------------
    rapido = {
        "Bike": calculate_fare(distance, 10, 4, surge),
        "Auto": calculate_fare(distance, 20, 6, surge),
        "Car":  calculate_fare(distance, 30, 8, surge)
    }

    ola = {
        "Bike": calculate_fare(distance, 15, 5, surge),
        "Auto": calculate_fare(distance, 30, 8, surge),
        "Car":  calculate_fare(distance, 45, 11, surge)
    }

    uber = {
        "Bike": calculate_fare(distance, 20, 6, surge),
        "Auto": calculate_fare(distance, 35, 9, surge),
        "Car":  calculate_fare(distance, 55, 13, surge)
    }

    # -----------------------------
    # API Response
    # -----------------------------
    return {
        "metrics": {
            "distance_km": round(distance / 1000, 2),
            "demand": demand,
            "supply": supply,
            "surge": surge,
            "system_time": datetime.now().strftime("%H:%M:%S"),
            "time_increment": time_increment()
        },
        "fares": {
            "rapido": rapido,
            "ola": ola,
            "uber": uber
        },
        "path": route_coords,
        "start_coords": [lat1, lon1],
        "end_coords": [lat2, lon2]
    }