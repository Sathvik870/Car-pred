import streamlit as st
import osmnx as ox
import networkx as nx
import requests
import random
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Ride Comparison Simulator", layout="wide")
st.title("Dynamic Ride-Hailing Pricing Simulator")

# ---------------------------------------------------
# SESSION INIT
# ---------------------------------------------------
if "ride_data" not in st.session_state:
    st.session_state.ride_data = None


# ---------------------------------------------------
# GEOCODING
# ---------------------------------------------------
def get_coordinates(place):
    if place.strip() == "":
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "college-project"}
    params = {"q": place, "format": "json", "limit": 1}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if len(data) == 0:
            return None, None

        return float(data[0]['lat']), float(data[0]['lon'])
    except:
        return None, None


# ---------------------------------------------------
# SURGE MODEL
# ---------------------------------------------------
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


# ---------------------------------------------------
# FARE FORMULA
# ---------------------------------------------------
def calculate_fare(distance_meters, base, per_km, surge):
    distance_km = distance_meters / 1000
    fare = base + (distance_km * per_km)
    return round(fare * surge, 2)


# ---------------------------------------------------
# USER INPUT
# ---------------------------------------------------
pickup = st.text_input("Enter Pickup Location")
drop = st.text_input("Enter Drop Location")

if st.button("Compare Fares"):

    if pickup.strip() == "" or drop.strip() == "":
        st.error("Please enter both pickup and drop locations.")
        st.stop()

    with st.spinner("Calculating route and fares..."):

        lat1, lon1 = get_coordinates(pickup)
        lat2, lon2 = get_coordinates(drop)

        if lat1 is None or lat2 is None:
            st.error("Invalid location entered.")
            st.stop()

        try:
            G = ox.graph_from_point((lat1, lon1), dist=7000, network_type='drive')
            orig_node = ox.nearest_nodes(G, lon1, lat1)
            dest_node = ox.nearest_nodes(G, lon2, lat2)

            route = nx.shortest_path(G, orig_node, dest_node, weight='length')
            distance = nx.shortest_path_length(G, orig_node, dest_node, weight='length')

        except:
            st.error("Route not found.")
            st.stop()

        demand = random.randint(50, 120)
        supply = random.randint(30, 100)
        surge = surge_multiplier(demand, supply)

        # ---------------------------
        # PLATFORM PRICING STRATEGY
        # ---------------------------

        # RAPIDO (cheapest)
        rapido = {
            "Bike": calculate_fare(distance, 10, 4, surge),
            "Auto": calculate_fare(distance, 20, 6, surge),
            "Car":  calculate_fare(distance, 30, 8, surge)
        }

        # OLA (medium)
        ola = {
            "Bike": calculate_fare(distance, 15, 5, surge),
            "Auto": calculate_fare(distance, 30, 8, surge),
            "Car":  calculate_fare(distance, 45, 11, surge)
        }

        # UBER (premium)
        uber = {
            "Bike": calculate_fare(distance, 20, 6, surge),
            "Auto": calculate_fare(distance, 35, 9, surge),
            "Car":  calculate_fare(distance, 55, 13, surge)
        }

        st.session_state.ride_data = {
            "G": G,
            "route": route,
            "distance": distance,
            "demand": demand,
            "supply": supply,
            "surge": surge,
            "rapido": rapido,
            "ola": ola,
            "uber": uber
        }


# ---------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------
if st.session_state.ride_data:

    data = st.session_state.ride_data

    st.success("Comparison Generated Successfully")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ride Details")
        st.write("Distance (km):", round(data["distance"] / 1000, 2))
        st.write("Demand:", data["demand"])
        st.write("Supply:", data["supply"])
        st.write("Surge Multiplier:", data["surge"])

        st.markdown("---")

        st.subheader("Rapido")
        st.write("Bike: ₹", data["rapido"]["Bike"])
        st.write("Auto: ₹", data["rapido"]["Auto"])
        st.write("Car: ₹", data["rapido"]["Car"])

        st.markdown("---")

        st.subheader("Ola")
        st.write("Bike: ₹", data["ola"]["Bike"])
        st.write("Auto: ₹", data["ola"]["Auto"])
        st.write("Car: ₹", data["ola"]["Car"])

        st.markdown("---")

        st.subheader("Uber")
        st.write("Bike: ₹", data["uber"]["Bike"])
        st.write("Auto: ₹", data["uber"]["Auto"])
        st.write("Car: ₹", data["uber"]["Car"])

    with col2:
        st.subheader("Route Map")

        route_coords = [
            (data["G"].nodes[node]['y'], data["G"].nodes[node]['x'])
            for node in data["route"]
        ]

        route_map = folium.Map(location=route_coords[0], zoom_start=13)
        folium.PolyLine(route_coords, weight=5).add_to(route_map)

        folium.Marker(route_coords[0], popup="Pickup").add_to(route_map)
        folium.Marker(route_coords[-1], popup="Drop").add_to(route_map)

        st_folium(route_map, width=600)