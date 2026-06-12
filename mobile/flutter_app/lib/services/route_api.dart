import 'dart:convert';
import 'package:http/http.dart' as http;

class RouteApi {
  static const baseUrl = "http://localhost:8000";

  static Future<Map<String, dynamic>> findRoute(String query) async {
    final res = await http.post(
      Uri.parse("$baseUrl/route"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"query": query}),
    );

    if (res.statusCode != 200) {
      throw Exception(res.body);
    }

    return jsonDecode(res.body);
  }
}