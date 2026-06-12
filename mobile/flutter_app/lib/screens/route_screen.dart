import 'package:flutter/material.dart';
import '../services/route_api.dart';
import '../widgets/route_map.dart';

class RouteScreen extends StatefulWidget {
  const RouteScreen({super.key});

  @override
  State<RouteScreen> createState() => _RouteScreenState();
}

class _RouteScreenState extends State<RouteScreen> {
  final controller = TextEditingController();

  Map<String, dynamic>? route;

  Future<void> search() async {
    final data = await RouteApi.findRoute(controller.text);

    setState(() {
      route = data;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Metro Route Finder")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(22),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    decoration: const InputDecoration(
                      labelText: "Query",
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: search,
                )
              ],
            ),
          ),
          Expanded(
            child: MetroMap(routeData: route),
          )
        ],
      ),
    );
  }
}