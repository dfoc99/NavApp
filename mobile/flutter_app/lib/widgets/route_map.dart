import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MetroMap extends StatelessWidget {
  final Map<String, dynamic>? routeData;
  final MapController? mapController; // 👈 novo parâmetro

  const MetroMap({super.key, this.routeData, this.mapController});

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
      // Estações
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
            width: 19,
            height: 19,
            child: Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color:color,
                border: Border.all(width: 1, color: const Color.fromARGB(255, 68, 68, 68)),
              ),
            ),
          ),
        );
          
        // Marcador da label (deslocada para baixo)
        markers.add(
          Marker(
            point: LatLng(s["lat"], s["lon"]),
            width: 100,
            height: 30,
            alignment: const Alignment(1.2, 0.9), // label fica à direita do ponto
            child: Container(
              alignment: Alignment.center, 
              padding: const EdgeInsets.symmetric(horizontal: 1, vertical: 1),
              decoration: const BoxDecoration(
                color: Color.fromRGBO(255, 255, 255, 0.85),
                borderRadius: BorderRadius.all(Radius.circular(8)),
                border: Border.fromBorderSide(BorderSide(width: 1, color: Color.fromARGB(255, 68, 68, 68))),
              ),
              child: Text(
                s["name"],
                style: const TextStyle(fontSize: 13),
                textAlign: TextAlign.center,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
        );
        }

      // -------------------
      // Linhas entre estações
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
      mapController: mapController,
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