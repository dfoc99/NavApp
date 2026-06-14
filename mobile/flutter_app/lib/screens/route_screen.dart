import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
// import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:flutter_map_animations/flutter_map_animations.dart';

import '../services/route_api.dart';
import '../widgets/route_map.dart';


class RouteScreen extends StatefulWidget {
  const RouteScreen({super.key});

  @override
  State<RouteScreen> createState() => _RouteScreenState();
}


class _RouteScreenState extends State<RouteScreen>
      with TickerProviderStateMixin {

  final controller = TextEditingController();
  late final mapController = AnimatedMapController(vsync: this);
  Map<String, dynamic>? route;
  LatLng? userPosition;

  @override
  void initState() {
    super.initState();
    _centerOnUser();
  }

  Future<void> _centerOnUser() async {
    try {
      final status = await Geolocator.checkPermission();
      if (status == LocationPermission.denied) {
        final req = await Geolocator.requestPermission();
        if (req == LocationPermission.denied) return;
      }

      if (await Geolocator.isLocationServiceEnabled()) {
        final pos = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.best);
        setState(() {
          userPosition = LatLng(pos.latitude, pos.longitude);
        });
        mapController.animateTo(
          dest: LatLng(pos.latitude, pos.longitude),
          zoom: 14.0,
          duration: const Duration(milliseconds: 900),
          curve: Curves.easeInOut,
        );
      }
    } catch (_) {
      // ignore errors silently; fallback to default map center
    }
  }

  Future<void> search() async {
    final data = await RouteApi.findRoute(controller.text);

    setState(() {
      route = data;
    });

    final stations = data["stations"] as List;
    if (stations.isNotEmpty) {
      final first = stations.first;

      mapController.animateTo(
        dest: LatLng(first["lat"], first["lon"]),
        zoom: 15.0,
        duration: const Duration(milliseconds: 800),
        curve: Curves.easeInOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Shortest Path Finder")),
      body: SingleChildScrollView(
        child: Column(
          children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    onSubmitted: (_) => search(),
                    style: const TextStyle(fontFamily: 'Roboto', fontSize: 16),
                    decoration: InputDecoration(
                      hintText: "Para onde queres ir?",
                      hintStyle: const TextStyle(fontFamily: 'Roboto', fontSize: 16),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(18),
                      ),
                      filled: true,
                      fillColor: Colors.white,
                      prefixIcon: IconButton(
                        icon: const Icon(Icons.search),
                        onPressed: search,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Results summary (antes do mapa)
          if (route != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("Rota", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          const Text("Origem: ", style: TextStyle(fontWeight: FontWeight.w600)),
                          Expanded(child: Text(route!["origin"] ?? "-", style: const TextStyle(fontSize: 14))),
                          const SizedBox(width: 12),
                          const Text("Destino: ", style: TextStyle(fontWeight: FontWeight.w600)),
                          Expanded(child: Text(route!["destination"] ?? "-", style: const TextStyle(fontSize: 14))),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text("Duração: ${route!["arrival_time_human"] ?? "-"}", style: const TextStyle(fontSize: 14)),
                      const SizedBox(height: 8),
                      // Mostrar apenas segmentos no formato: Origem -> Destino (linha X)
                      Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Builder(builder: (context) {
                          final segs = route!["segments"] as List?;
                          final stations = route!["stations"] as List;

                          if (segs == null || segs.isEmpty) {
                            return const Text("(Sem segmentos)");
                          }

                          // Agrupar segmentos consecutivos pela mesma linha
                          List<Map<String, String>> groups = [];

                          if (segs.isNotEmpty) {
                            String currentLine = (segs[0]["line"] ?? "").toString();
                            String startId = (segs[0]["from"] ?? "").toString();
                            String endId = (segs[0]["to"] ?? "").toString();

                            for (int i = 1; i < segs.length; i++) {
                              final s = segs[i];
                              final line = (s["line"] ?? "").toString();
                              final from = (s["from"] ?? "").toString();
                              final to = (s["to"] ?? "").toString();

                              if (line == currentLine) {
                                // estende o fim do trecho
                                endId = to;
                              } else {
                                groups.add({"line": currentLine, "from": startId, "to": endId});
                                currentLine = line;
                                startId = from;
                                endId = to;
                              }
                            }

                            // adiciona o último grupo
                            groups.add({"line": currentLine, "from": startId, "to": endId});
                          }

                          String findName(String id) {
                            try {
                              final s = stations.firstWhere((st) => st["id"].toString() == id);
                              return s["name"] ?? id;
                            } catch (_) {
                              return id;
                            }
                          }

                          final items = groups.map<Widget>((g) {
                            final fromName = findName(g["from"] ?? "");
                            final toName = findName(g["to"] ?? "");
                            final line = g["line"] ?? "--";

                            return Padding(
                              padding: const EdgeInsets.only(bottom: 6),
                              child: Text(
                                "$fromName -> $toName ($line)",
                                style: const TextStyle(fontSize: 14),
                              ),
                            );
                          }).toList();

                          return Column(crossAxisAlignment: CrossAxisAlignment.start, children: items);
                        }),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Mapa no fim da página (o utilizador faz scroll até ao mapa)
          SizedBox(
            height: MediaQuery.of(context).size.height * 0.58,
            child: MetroMap(
              routeData: route,
              mapController: mapController.mapController,
              userLocation: userPosition,
            ),
          ),
        ],
      ),
    ),
    );
  }
}