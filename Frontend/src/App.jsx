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
      setError(err.response?.data?.detail || "Network Error: Ensure Backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans text-gray-800">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-extrabold text-center text-blue-900 mb-8 tracking-tight">
          Ride-Hailing Simulator
        </h1>
        <div className="bg-white p-6 rounded-2xl shadow-lg mb-8 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-bold text-gray-600 mb-1">Pickup</label>
            <input
              type="text"
              value={pickup}
              onChange={(e) => setPickup(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
              placeholder="e.g. Times Square"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-600 mb-1">Drop</label>
            <input
              type="text"
              value={drop}
              onChange={(e) => setDrop(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
              placeholder="e.g. Central Park"
            />
          </div>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition shadow-md disabled:bg-blue-300"
          >
            {loading ? "Simulating..." : "Calculate Estimates"}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-8 rounded">
            {error}
          </div>
        )}
        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-3 space-y-4">
              <div className="bg-white p-5 rounded-2xl shadow-md border-t-4 border-blue-500">
                <h3 className="text-lg font-bold text-gray-800 mb-3 border-b pb-2">Trip Details</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Distance</span>
                    <span className="font-bold">{data.metrics.distance_km} km</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">System Time</span>
                    <span className="font-bold">{data.metrics.system_time}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Surge Level</span>
                    <span className={`px-2 py-0.5 rounded text-sm font-bold ${data.metrics.surge > 1 ? 'bg-orange-100 text-orange-600' : 'bg-green-100 text-green-600'}`}>
                      {data.metrics.surge}x
                    </span>
                  </div>
                  <div className="flex justify-between">
                     <span className="text-gray-500">Demand/Supply</span>
                     <span className="font-bold">{data.metrics.demand} / {data.metrics.supply}</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="lg:col-span-5 space-y-5">
              {["rapido", "uber", "ola"].map((provider) => (
                <div 
                  key={provider} 
                  className={`bg-white rounded-2xl shadow-md overflow-hidden border border-gray-100 transition hover:shadow-lg
                    ${provider === 'rapido' ? 'border-l-8 border-l-yellow-400' : 
                      provider === 'uber' ? 'border-l-8 border-l-black' : 
                      'border-l-8 border-l-lime-500'}`}
                >
                  <div className="px-5 py-3 bg-gray-50 border-b flex justify-between items-center">
                    <h3 className="text-xl font-extrabold capitalize text-gray-800">{provider}</h3>
                    {provider === 'rapido' && <span className="text-xs font-bold text-white bg-yellow-500 px-2 py-1 rounded-full">RECOMMENDED</span>}
                  </div>

                  <div className="p-4 space-y-3">
                    {Object.entries(data.estimates[provider]).map(([vehicle, details]) => (
                      <div key={vehicle} className="flex justify-between items-center border-b border-dashed border-gray-200 pb-2 last:border-0 last:pb-0">
                        <div className="flex items-center gap-3 w-1/4">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white
                            ${vehicle === 'Bike' ? 'bg-blue-400' : vehicle === 'Auto' ? 'bg-yellow-500' : 'bg-green-500'}`}>
                            {vehicle[0]}
                          </div>
                          <span className="font-semibold text-gray-700">{vehicle}</span>
                        </div>
                        <div className="text-lg font-bold text-gray-800 w-1/4">
                          ₹{details.price}
                        </div>
                        <div className="flex flex-col items-end w-1/2">
                          <span className="text-sm font-medium text-gray-600">
                             ⏱ {details.eta} mins
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-bold mt-1
                            ${details.prob > 80 ? 'bg-green-100 text-green-700' : 
                              details.prob > 50 ? 'bg-yellow-100 text-yellow-700' : 
                              'bg-red-100 text-red-700'}`}>
                            {details.prob}% Chance
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="lg:col-span-4 h-96 lg:h-auto">
              {data.start && data.end ? (
                <div className="h-full bg-white p-2 rounded-2xl shadow-md overflow-hidden relative z-0 border border-gray-200">
                   <MapContainer 
                      center={data.start} 
                      zoom={13} 
                      scrollWheelZoom={false} 
                      className="h-full w-full rounded-xl"
                    >
                    <TileLayer
                      attribution='&copy; OpenStreetMap'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={data.start}><Popup>Pickup</Popup></Marker>
                    <Marker position={data.end}><Popup>Drop</Popup></Marker>
                    <Polyline positions={data.path} color="#2563EB" weight={6} />
                    <MapUpdater coords={data.path} />
                  </MapContainer>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center bg-gray-100 rounded-2xl text-gray-400">
                  Map Preview
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
}

export default App;