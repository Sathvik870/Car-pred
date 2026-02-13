from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import osmnx as ox
import networkx as nx
import requests
import random
from datetime import datetime
from geopy.distance import geodesic
app = FastAPI()

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
    if not place or place.strip() == "": return None, None
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "ride-simulator-project"}
    params = {"q": place, "format": "json", "limit": 1}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        return (float(data[0]['lat']), float(data[0]['lon'])) if data else (None, None)
    except:
        return None, None

def surge_multiplier(demand, supply):
    if supply == 0: return 2.0
    ratio = demand / supply
    return 1.0 if ratio < 1 else (1.2 if ratio < 1.5 else (1.5 if ratio < 2 else 2.0))

def time_increment():
    hour = datetime.now().hour
    if 0 <= hour < 6: return 100
    elif 6 <= hour < 10: return 20
    elif 10 <= hour < 15: return 30
    elif 15 <= hour < 21: return 0
    elif 21 <= hour <= 23: return 30
    return 0

def calculate_base_fare(distance_meters, base, per_km, surge):
    distance_km = distance_meters / 1000
    base_price = base + time_increment()
    fare = base_price + (distance_km * per_km)
    return round(fare * surge, 2)

def get_time_based_base_stats():
    """Returns the raw 'Bike' stats based on time of day."""
    hour = datetime.now().hour
    prob = 50
    eta = 10
    
    if 0 <= hour < 6:      # Late Night
        prob = random.uniform(20, 40)
        eta = random.randint(15, 25)
    elif 6 <= hour < 10:   # Morning Peak
        prob = random.uniform(40, 60)
        eta = random.randint(10, 15)
    elif 10 <= hour < 15:  # Mid Day
        prob = random.uniform(70, 90)
        eta = random.randint(5, 10)
    elif 15 <= hour < 21:  # Evening Peak
        prob = random.uniform(60, 80)
        eta = random.randint(8, 12)
    elif 21 <= hour <= 23: # Night
        prob = random.uniform(50, 70)
        eta = random.randint(10, 15)
        
    return prob, eta

def generate_ride_option(distance, surge, vehicle_type, provider):
    """
    Calculates Price, ETA, and Probability specific to:
    1. Vehicle Type (Bike/Auto/Car)
    2. Provider (Rapido > Uber > Ola)
    """
    
    if vehicle_type == "Bike":
        price = calculate_base_fare(distance, 10, 4, surge)
        base_prob, base_eta = get_time_based_base_stats() 
    elif vehicle_type == "Auto":
        price = calculate_base_fare(distance, 20, 6, surge)
        base_prob, base_eta = get_time_based_base_stats()
        base_prob -= 10 
        base_eta += 2  
    else: # Car
        price = calculate_base_fare(distance, 30, 8, surge)
        base_prob, base_eta = get_time_based_base_stats()
        base_prob += 20 
        base_eta -= 2 

    if provider == "rapido":
        price_mod = 1.0 
        prob_mod = 15  
        eta_mod = -3   
    elif provider == "uber":
        price_mod = 1.3
        prob_mod = 5
        eta_mod = -1
    else: 
        price_mod = 1.2
        prob_mod = -10
        eta_mod = 3   

    final_price = round(price * price_mod, 2)
    final_prob = max(10, min(99, int(base_prob + prob_mod))) 
    final_eta = max(2, int(base_eta + eta_mod))

    return {
        "price": final_price,
        "eta": final_eta,
        "prob": final_prob
    }

@app.post("/api/calculate-ride")
async def calculate_ride(request: RideRequest):
    lat1, lon1 = get_coordinates(request.pickup)
    lat2, lon2 = get_coordinates(request.drop)

    if not lat1 or not lat2:
        raise HTTPException(status_code=400, detail="Invalid locations.")

    # try:
    #     G = ox.graph_from_point((lat1, lon1), dist=10000, network_type='drive')
    #     orig = ox.nearest_nodes(G, lon1, lat1)
    #     dest = ox.nearest_nodes(G, lon2, lat2)
    #     route = nx.shortest_path(G, orig, dest, weight='length')
    #     distance = nx.shortest_path_length(G, orig, dest, weight='length')
    #     route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
    try:
        straight_distance_km = geodesic((lat1, lon1), (lat2, lon2)).km
        buffer_km = 5
        graph_radius_m = (straight_distance_km + buffer_km) * 1000

        G = ox.graph_from_point(
            (lat1, lon1),
            dist=graph_radius_m,
            network_type='drive'
        )
        orig = ox.nearest_nodes(G, lon1, lat1)
        dest = ox.nearest_nodes(G, lon2, lat2)
        route = nx.shortest_path(G, orig, dest, weight='length')
        distance = nx.shortest_path_length(G, orig, dest, weight='length')
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Route not found.")

    demand = random.randint(50, 120)
    supply = random.randint(30, 100)
    surge = surge_multiplier(demand, supply)
    providers = ["rapido", "uber", "ola"]
    vehicles = ["Bike", "Auto", "Car"]
    
    results = {}

    for prov in providers:
        results[prov] = {}
        for veh in vehicles:
            results[prov][veh] = generate_ride_option(distance, surge, veh, prov)

    return {
        "metrics": {
            "distance_km": round(distance / 1000, 2),
            "surge": surge,
            "demand": demand,
            "supply": supply,
            "system_time": datetime.now().strftime("%H:%M")
        },
        "estimates": results,
        "path": route_coords,
        "start": [lat1, lon1],
        "end": [lat2, lon2]
    }