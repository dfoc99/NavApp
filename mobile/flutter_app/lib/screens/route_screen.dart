import 'package:flutter/material.dart';
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
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(22),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    decoration: InputDecoration(
                      hintText: "Para onde queres ir?",
                      // labelText: "Query",
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    prefixIcon: IconButton(
                      icon: const Icon(Icons.search),
                      onPressed: search,
                      )
                    ),
                  ),
                ),

              ],
            ),
          ),
          Expanded(
            child: MetroMap(
              routeData: route,
              mapController: mapController.mapController,
            ),
          )
        ],
      ),
    );
  }
}