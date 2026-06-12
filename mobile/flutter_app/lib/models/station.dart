class Station {
  final String id;
  final String name;
  final double lat;
  final double lon;

  Station({
    required this.id,
    required this.name,
    required this.lat,
    required this.lon,
  });

  factory Station.fromJson(Map<String, dynamic> json) {
    return Station(
      id: json["id"],
      name: json["name"],
      lat: (json["lat"] as num).toDouble(),
      lon: (json["lon"] as num).toDouble(),
    );
  }
}