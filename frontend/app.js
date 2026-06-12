const API = "http://localhost:8000";

let map;
let polylineLayer;
let markerLayer;

// -----------------------
// LINE COLORS
// -----------------------
const LINE_COLORS = {
  "Vermelha": "#e53935",
  "Verde": "#43a047",
  "Azul": "#1e88e5",
  "Amarela": "#fdd835"
};

// -----------------------
function initMap() {
  map = L.map("mapid").setView([38.743, -9.12], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap"
  }).addTo(map);

  // -----------------------
  // PANES (Z-INDEX CONTROL)
  // -----------------------
  map.createPane("linesPane");
  map.getPane("linesPane").style.zIndex = 350;

  map.createPane("markersPane");
  map.getPane("markersPane").style.zIndex = 650;

  map.createPane("labelsPane");
  map.getPane("labelsPane").style.zIndex = 700;

  polylineLayer = L.layerGroup().addTo(map);
  markerLayer = L.layerGroup().addTo(map);
}

window.onload = initMap;

// -----------------------
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

    document.getElementById("result").textContent =
      JSON.stringify(data, null, 2);

    renderRoute(data.stations, data.segments);

  } catch (err) {
    document.getElementById("result").textContent =
      "Network error: " + err.message;
  }
}

// -----------------------
// HELPERS
// -----------------------
function formatMinutes(t) {
  if (t == null) return "";
  return `${Math.round(t)} min`;
}

// -----------------------
// MAP RENDER
// -----------------------
function renderRoute(stations, segments) {
  if (!stations || stations.length === 0) return;

  polylineLayer.clearLayers();
  markerLayer.clearLayers();

  const stationMap = {};
  stations.forEach(s => stationMap[s.id] = s);

  // -----------------------
  // MARKERS (station names ALWAYS visible)
  // -----------------------
  stations.forEach((s, i) => {
    let color = "blue";
    if (i === 0) color = "green";
    else if (i === stations.length - 1) color = "red";

    L.circleMarker([s.lat, s.lon], {
      radius: 6,
      color,
      fillOpacity: 0.9
    })
      .addTo(markerLayer)
      .bindPopup(`<b>${s.name}</b><br>${s.id}`)

      // ALWAYS VISIBLE LABEL (no hover)
      .bindTooltip(s.name, {
        permanent: true,
        direction: "top",
        offset: [0, -10],
        className: "station-label"
      });
  });

  // -----------------------
  // SEGMENTS (REAL LINE COLORS + ALWAYS VISIBLE TIME LABELS)
  // -----------------------
  if (segments && segments.length > 0) {
    segments.forEach(seg => {
      const color = LINE_COLORS[seg.line] || "#9e9e9e";

      const line = L.polyline(seg.coords, {
        color,
        weight: 5,
        opacity: 0.9
      }).addTo(polylineLayer);

      // edge time ALWAYS visible (midpoint label)
      if (seg.time != null) {
        const midLat = (seg.coords[0][0] + seg.coords[1][0]) / 2;
        const midLon = (seg.coords[0][1] + seg.coords[1][1]) / 2;

        L.marker([midLat, midLon], {
          icon: L.divIcon({
            className: "edge-label",
            html: `<div>${formatMinutes(seg.time)}</div>`,
            iconSize: [60, 20],
            iconAnchor: [30, 10]
          })
        }).addTo(polylineLayer);
      }
    });
  } else {
    const coords = stations.map(s => [s.lat, s.lon]);
    const line = L.polyline(seg.coords, {
    color,
    weight: 5,
    opacity: 0.9,
    pane: "linesPane"
    }).addTo(polylineLayer);
  }

  // -----------------------
  // FIT MAP
  // -----------------------
  const bounds = L.polyline(stations.map(s => [s.lat, s.lon])).getBounds();
  map.fitBounds(bounds);
}