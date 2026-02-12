import { useState } from "react";
import axios from "axios";
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

function MapUpdater({ coords }) {
  const map = useMap();
  if (coords && coords.length > 0) {
    map.fitBounds(coords);
  }
  return null;
}

function App() {
  const [pickup, setPickup] = useState("");
  const [drop, setDrop] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const handleCompare = async () => {
    if (!pickup || !drop) {
      setError("Please enter both locations.");
      return;
    }
    setError("");
    setLoading(true);
    setData(null);

    try {
      const response = await axios.post("http://localhost:8000/api/calculate-ride", {
        pickup: pickup,
        drop: drop,
      });
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "An error occurred while fetching data.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8 font-sans text-gray-800">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-blue-700 mb-8">
          Ride-Hailing Pricing Simulator
        </h1>

        {/* INPUT SECTION */}
        <div className="bg-white p-6 rounded-xl shadow-md mb-8 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-semibold mb-2">Pickup Location</label>
            <input
              type="text"
              value={pickup}
              onChange={(e) => setPickup(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Times Square"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-2">Drop Location</label>
            <input
              type="text"
              value={drop}
              onChange={(e) => setDrop(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Central Park"
            />
          </div>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition disabled:bg-blue-300"
          >
            {loading ? "Calculating..." : "Compare Fares"}
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-8">
            <p>{error}</p>
          </div>
        )}

        {/* RESULTS SECTION */}
        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* LEFT COL: METRICS & PRICES */}
            <div className="space-y-6">
              
              {/* Metrics */}
              <div className="bg-white p-4 rounded-xl shadow-md flex justify-between text-center">
                <div>
                  <p className="text-xs text-gray-500 uppercase">Distance</p>
                  <p className="font-bold text-lg">{data.metrics.distance_km} km</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase">Demand</p>
                  <p className="font-bold text-lg">{data.metrics.demand}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase">Supply</p>
                  <p className="font-bold text-lg">{data.metrics.supply}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase">Surge</p>
                  <p className="font-bold text-lg text-orange-600">x{data.metrics.surge}</p>
                </div>
              </div>

              {/* Pricing Cards */}
              <div className="space-y-4">
                {["rapido", "ola", "uber"].map((provider) => (
                  <div key={provider} className="bg-white p-5 rounded-xl shadow-md border-l-8 border-blue-500">
                    <h3 className="text-xl font-bold capitalize mb-3 text-gray-800 border-b pb-2">
                      {provider}
                    </h3>
                    <div className="grid grid-cols-3 gap-4">
                      {Object.entries(data.fares[provider]).map(([vehicle, price]) => (
                        <div key={vehicle} className="text-center">
                          <p className="text-sm text-gray-500">{vehicle}</p>
                          <p className="text-lg font-semibold">₹ {price}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* RIGHT COL: MAP */}
            <div className="h-96 lg:h-auto bg-white p-2 rounded-xl shadow-md overflow-hidden relative z-0">
               <MapContainer 
                  center={data.start_coords} 
                  zoom={13} 
                  scrollWheelZoom={false} 
                  className="h-full w-full rounded-lg"
                >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                
                <Marker position={data.start_coords}>
                  <Popup>Pickup</Popup>
                </Marker>
                
                <Marker position={data.end_coords}>
                  <Popup>Drop</Popup>
                </Marker>
                
                {/* Route Polyline */}
                <Polyline positions={data.path} color="blue" weight={5} />
                
                {/* Auto-zoom helper */}
                <MapUpdater coords={data.path} />
              </MapContainer>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}

export default App;