const API = "http://localhost:8000";

let map;
let polylineLayer;
let markerLayer;

function initMap() {
  map = L.map("mapid").setView([38.743, -9.12], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap"
  }).addTo(map);

  polylineLayer = L.layerGroup().addTo(map);
  markerLayer = L.layerGroup().addTo(map);

  setTimeout(() => map.invalidateSize(), 300);
}

async function findRoute() {
  const query = document.getElementById("query").value;

  try {
    const res = await fetch(`${API}/route`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    const data = await res.json();

    if (!res.ok) {
      document.getElementById("result").textContent =
        "Error: " + (data.detail || "unknown error");
      return;
    }

    // Build display text
    let displayText = "";

    if (data.route_string) {
      displayText += data.route_string + "\n\n";
    }

    if (data.arrival_time_human) {
      displayText += `Arrival time: ${data.arrival_time_human}\n\n`;
    }

    displayText += JSON.stringify(data, null, 2);

    document.getElementById("result").textContent = displayText;

    renderRoute(data.stations);

  } catch (err) {
    document.getElementById("result").textContent =
      "Network error: " + err.message;
  }
}

function renderRoute(stations) {
  if (!stations || stations.length === 0) return;

  polylineLayer.clearLayers();
  markerLayer.clearLayers();

  const coords = stations.map(s => [s.lat, s.lon]);

  // -----------------------
  // Markers
  // -----------------------
  stations.forEach((s, i) => {
    let color = "blue";

    if (i === 0) color = "green";
    else if (i === stations.length - 1) color = "red";

    L.circleMarker([s.lat, s.lon], {
      radius: 7,
      color,
      fillColor: color,
      fillOpacity: 0.9
    })
      .addTo(markerLayer)
      .bindPopup(`${s.name} (${s.id})`);
  });

  // -----------------------
  // Segmented colored path
  // -----------------------
  for (let i = 0; i < coords.length - 1; i++) {
    let segmentColor = "blue";

    if (i === 0) segmentColor = "green";
    else if (i === coords.length - 2) segmentColor = "red";

    L.polyline([coords[i], coords[i + 1]], {
      color: segmentColor,
      weight: 5,
      opacity: 0.85
    }).addTo(polylineLayer);
  }

  // Fit map to route
  const boundsLine = L.polyline(coords);
  map.fitBounds(boundsLine.getBounds());
}

window.onload = initMap;