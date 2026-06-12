import 'package:flutter/material.dart';
import 'screens/route_screen.dart';

void main() {
  runApp(const MetroApp());
}

class MetroApp extends StatelessWidget {
  const MetroApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: RouteScreen(),
    );
  }
}