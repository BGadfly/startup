class AnalysisResult {
  final String comment;
  final List<PhotoAnalysis> photosAnalysis;
  final AggregatedData aggregated;
  final String partRecommendation;
  final String recommendedExtension;
  final String message;

  AnalysisResult({
    required this.comment,
    required this.photosAnalysis,
    required this.aggregated,
    required this.partRecommendation,
    required this.recommendedExtension,
    required this.message,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      comment: json['comment'],
      photosAnalysis: (json['photos_analysis'] as List)
          .map((e) => PhotoAnalysis.fromJson(e))
          .toList(),
      aggregated: AggregatedData.fromJson(json['aggregated']),
      partRecommendation: json['part_recommendation'],
      recommendedExtension: json['recommended_extension'],
      message: json['message'],
    );
  }
}

class PhotoAnalysis {
  final int photoIndex;
  final String filename;
  final String texture;
  final String density;
  final int partType;

  PhotoAnalysis({
    required this.photoIndex,
    required this.filename,
    required this.texture,
    required this.density,
    required this.partType,
  });

  factory PhotoAnalysis.fromJson(Map<String, dynamic> json) {
    return PhotoAnalysis(
      photoIndex: json['photo_index'],
      filename: json['filename'],
      texture: json['texture'],
      density: json['density'],
      partType: json['part_type'],
    );
  }
}

class AggregatedData {
  final String texture;
  final String density;
  final int partType;

  AggregatedData({
    required this.texture,
    required this.density,
    required this.partType,
  });

  factory AggregatedData.fromJson(Map<String, dynamic> json) {
    return AggregatedData(
      texture: json['texture'],
      density: json['density'],
      partType: json['part_type'],
    );
  }
}

String getPartTypeName(int partType) {
  switch (partType) {
    case 1: return 'Прямой пробор';
    case 2: return 'Боковой пробор';
    case 3: return 'Зигзагообразный пробор';
    case 4: return 'Отсутствие пробора';
    case 5: return 'Круговой пробор';
    default: return 'Неизвестно';
  }
}