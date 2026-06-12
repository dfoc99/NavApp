class Segment {
  final String line;
  final double? time;
  final List<List<double>> coords;

  Segment({
    required this.line,
    required this.time,
    required this.coords,
  });

  factory Segment.fromJson(Map<String, dynamic> json) {
    return Segment(
      line: json["line"] ?? "",
      time: json["time"] == null
          ? null
          : (json["time"] as num).toDouble(),
      coords: (json["coords"] as List)
          .map<List<double>>(
            (c) => [
              (c[0] as num).toDouble(),
              (c[1] as num).toDouble(),
            ],
          )
          .toList(),
    );
  }
}