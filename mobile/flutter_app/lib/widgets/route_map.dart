import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MetroMap extends StatelessWidget {
  final Map<String, dynamic>? routeData;

  const MetroMap({super.key, this.routeData});

  static const lineColors = {
    "Vermelha": Colors.red,
    "Verde": Colors.green,
    "Azul": Colors.blue,
    "Amarela": Colors.yellow,
  };

  @override
  Widget build(BuildContext context) {
    final markers = <Marker>[];
    final polylines = <Polyline>[];

    if (routeData != null) {
      final stations = routeData!["stations"] as List;

      // -------------------
      // MARKERS (stations)
      // -------------------
for (int i = 0; i < stations.length; i++) {
  final s = stations[i];

  final isStart = i == 0;
  final isEnd = i == stations.length - 1;

  final color = isStart
      ? Colors.green
      : isEnd
          ? Colors.red
          : Colors.blue;

  markers.add(
    Marker(
      point: LatLng(s["lat"], s["lon"]),
      width: 120,
      height: 50,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.circle,
            size: 15,
            color: color,
          ),

          const SizedBox(height: 2),

          // 👇 THIS is your permanent label
          Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 4,
                vertical: 1,
              ),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.95),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(width: 2),
              ),
              child: Text(
                s["name"],
                style: const TextStyle(
                  fontSize: 15,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }

      // -------------------
      // SEGMENTS (lines)
      // -------------------
      final segments = routeData!["segments"] as List?;

      if (segments != null) {
        for (final seg in segments) {
          final coords = seg["coords"] as List;

          polylines.add(
            Polyline(
              points: coords.map((c) {
                return LatLng(c[0], c[1]);
              }).toList(),
              strokeWidth: 8,
              color: lineColors[seg["line"]] ?? Colors.grey,
            ),
          );
        }
      }
    }

    return FlutterMap(
      options: const MapOptions(
        initialCenter: LatLng(38.743, -9.12),
        initialZoom: 15,
      ),
      children: [
        TileLayer(
          urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
          userAgentPackageName: 'com.navapp.flutter_app',
        ),
        PolylineLayer(polylines: polylines),
        MarkerLayer(markers: markers),
        const SimpleAttributionWidget(
          source: Text('OpenStreetMap contributors'),
          backgroundColor: Colors.white70,
        ),
      ],
    );
  }
}