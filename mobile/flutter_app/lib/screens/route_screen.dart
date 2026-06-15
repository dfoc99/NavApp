import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
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
  bool _resultsExpanded = false;

  static const double _collapsedFraction = 0.17;

  // Quando expandido, usa null para deixar o Flutter calcular a altura real do conteúdo.
  // Quando comprimido, usa uma fracção fixa do ecrã.
  double? _panelHeight(BuildContext context) {
    if (route == null) return null;
    if (_resultsExpanded) return null; // cresce até ao conteúdo real
    return MediaQuery.of(context).size.height * _collapsedFraction;
  }

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
        final pos = await Geolocator.getCurrentPosition(
            desiredAccuracy: LocationAccuracy.best);
        setState(() => userPosition = LatLng(pos.latitude, pos.longitude));
        mapController.animateTo(
          dest: LatLng(pos.latitude, pos.longitude),
          zoom: 14.0,
          duration: const Duration(milliseconds: 900),
          curve: Curves.easeInOut,
        );
      }
    } catch (_) {}
  }

  Future<void> search() async {
    final data = await RouteApi.findRoute(controller.text);

    setState(() {
      route = data;
      _resultsExpanded = true;
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

  Color _getLineColor(String line) {
    return MetroMap.lineColors[line] ?? const Color(0xFF666666);
  }

  @override
  Widget build(BuildContext context) {
    final panelHeight = _panelHeight(context);

    return Scaffold(
      appBar: AppBar(title: const Text("Shortest Path Finder")),
      body: Column(
        children: [
          // ── Painel de resultados com altura animada ──────────────────────
          AnimatedContainer(
            duration: const Duration(milliseconds: 350),
            curve: Curves.easeInOut,
            height: panelHeight,
            clipBehavior: _resultsExpanded ? Clip.none : Clip.hardEdge,
            decoration: const BoxDecoration(),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Search field — sempre visível
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: controller,
                          onSubmitted: (_) => search(),
                          style: const TextStyle(
                              fontFamily: 'Roboto', fontSize: 16),
                          decoration: InputDecoration(
                            hintText: "Para onde queres ir?",
                            hintStyle: const TextStyle(
                                fontFamily: 'Roboto', fontSize: 16),
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

                // Card de resultados — só aparece quando há rota
                if (route != null)
                  Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 4),
                    child: Card(
                      elevation: 2,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                            // ── Header — SEMPRE VISÍVEL ────────────────────
                            InkWell(
                              onTap: () => setState(
                                  () => _resultsExpanded = !_resultsExpanded),
                              borderRadius: const BorderRadius.vertical(
                                  top: Radius.circular(12)),
                              child: Padding(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 10),
                                child: Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text("Rota",
                                        style: TextStyle(
                                            fontWeight: FontWeight.w600,
                                            fontSize: 16)),
                                    Row(
                                      children: [
                                        // Duração visível quando comprimido
                                        if (!_resultsExpanded)
                                          Padding(
                                            padding: const EdgeInsets.only(
                                                right: 8),
                                            child: Text(
                                              route!["arrival_time_human"] ??
                                                  "-",
                                              style: const TextStyle(
                                                  fontSize: 13,
                                                  color: Colors.grey),
                                            ),
                                          ),
                                        Icon(_resultsExpanded
                                            ? Icons.expand_less
                                            : Icons.expand_more),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ),

                            const Divider(height: 1),

                            // ── Corpo — sem scroll, altura calculada dinamicamente
                            if (_resultsExpanded)
                              Padding(
                                padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
                                child: _buildRouteDetails(),
                              ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // ── Mapa — ocupa o resto ─────────────────────────────────────────
          Expanded(
            child: MetroMap(
              routeData: route,
              mapController: mapController.mapController,
              userLocation: userPosition,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRouteDetails() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text("Origem: ",
                style: TextStyle(fontWeight: FontWeight.w600)),
            Expanded(
                child: Text(route!["origin"] ?? "-",
                    style: const TextStyle(fontSize: 14))),
            const SizedBox(width: 12),
            const Text("Destino: ",
                style: TextStyle(fontWeight: FontWeight.w600)),
            Expanded(
                child: Text(route!["destination"] ?? "-",
                    style: const TextStyle(fontSize: 14))),
          ],
        ),
        const SizedBox(height: 6),
        Text("Duração: ${route!["arrival_time_human"] ?? "-"}",
            style: const TextStyle(fontSize: 14)),
        const SizedBox(height: 12),
        _buildSegments(),
      ],
    );
  }

  Widget _buildSegments() {
    final segs = route!["segments"] as List?;
    final stations = route!["stations"] as List;

    if (segs == null || segs.isEmpty) {
      return const Text("(Sem segmentos)");
    }

    // Agrupa segmentos consecutivos pela mesma linha
    final List<Map<String, String>> groups = [];
    String currentLine = (segs[0]["line"] ?? "").toString();
    String startId = (segs[0]["from"] ?? "").toString();
    String endId = (segs[0]["to"] ?? "").toString();

    for (int i = 1; i < segs.length; i++) {
      final s = segs[i];
      final line = (s["line"] ?? "").toString();
      final to = (s["to"] ?? "").toString();
      if (line == currentLine) {
        endId = to;
      } else {
        groups.add({"line": currentLine, "from": startId, "to": endId});
        currentLine = line;
        startId = (s["from"] ?? "").toString();
        endId = to;
      }
    }
    groups.add({"line": currentLine, "from": startId, "to": endId});

    String findName(String id) {
      try {
        final s = stations.firstWhere((st) => st["id"].toString() == id);
        return s["name"] ?? id;
      } catch (_) {
        return id;
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: groups.map((g) {
        final fromName = findName(g["from"] ?? "");
        final toName = findName(g["to"] ?? "");
        final line = g["line"] ?? "--";
        final lineColor = _getLineColor(line);

        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: lineColor, width: 2),
              color: lineColor.withOpacity(0.1),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            child: Row(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration:
                      BoxDecoration(color: lineColor, shape: BoxShape.circle),
                  child: Center(
                    child: Text(line,
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 12)),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    "$fromName → $toName",
                    style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        color: lineColor),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}