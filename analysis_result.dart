// lib/models/hair_analysis.dart
import 'package:flutter/foundation.dart';

class AnalysisResult {
  final String comment;
  final Map<String, PhotoAnalysis> photosAnalysis;
  final AggregatedData aggregated;
  final ProblemZones problemZones;
  final Recommendation recommendation;
  final bool success;
  final String? error;

  AnalysisResult({
    required this.comment,
    required this.photosAnalysis,
    required this.aggregated,
    required this.problemZones,
    required this.recommendation,
    required this.success,
    this.error,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      comment: json['user_comment'] ?? '',
      photosAnalysis: _parsePhotosAnalysis(json['individual_analyses'] ?? {}),
      aggregated: AggregatedData.fromJson(json['analysis'] ?? {}),
      problemZones: ProblemZones.fromJson(json['problem_zones'] ?? {}),
      recommendation: Recommendation.fromJson(json['recommendation'] ?? {}),
      success: json['success'] ?? false,
      error: json['error'],
    );
  }

  static Map<String, PhotoAnalysis> _parsePhotosAnalysis(
    Map<String, dynamic> data,
  ) {
    final Map<String, PhotoAnalysis> result = {};

    if (data.containsKey('front')) {
      result['front'] = PhotoAnalysis.fromJson(data['front'], 'front');
    }
    if (data.containsKey('side')) {
      result['side'] = PhotoAnalysis.fromJson(data['side'], 'side');
    }
    if (data.containsKey('top')) {
      result['top'] = PhotoAnalysis.fromJson(data['top'], 'top');
    }

    return result;
  }

  Map<String, dynamic> toJson() {
    return {
      'user_comment': comment,
      'individual_analyses': {
        'front': photosAnalysis['front']?.toJson(),
        'side': photosAnalysis['side']?.toJson(),
        'top': photosAnalysis['top']?.toJson(),
      },
      'analysis': aggregated.toJson(),
      'problem_zones': problemZones.toJson(),
      'recommendation': recommendation.toJson(),
      'success': success,
      'error': error,
    };
  }
}

class PhotoAnalysis {
  final String viewType;
  final String texture;
  final String density;
  final String partType;
  final ProblemZones problemZones;

  PhotoAnalysis({
    required this.viewType,
    required this.texture,
    required this.density,
    required this.partType,
    required this.problemZones,
  });

  factory PhotoAnalysis.fromJson(Map<String, dynamic> json, String viewType) {
    return PhotoAnalysis(
      viewType: viewType,
      texture: json['texture'] ?? 'не определено',
      density: json['density'] ?? 'не определено',
      partType: json['part_type'] ?? 'прямой',
      problemZones: ProblemZones.fromJson(json['problem_zones'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'view_type': viewType,
      'texture': texture,
      'density': density,
      'part_type': partType,
      'problem_zones': problemZones.toJson(),
    };
  }
}

class AggregatedData {
  final String texture;
  final String density;
  final String partType;
  final ProblemZones problemZones;

  AggregatedData({
    required this.texture,
    required this.density,
    required this.partType,
    required this.problemZones,
  });

  factory AggregatedData.fromJson(Map<String, dynamic> json) {
    return AggregatedData(
      texture: json['texture'] ?? 'не определено',
      density: json['density'] ?? 'не определено',
      partType: json['part_type'] ?? 'прямой',
      problemZones: ProblemZones.fromJson(json['problem_zones'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'texture': texture,
      'density': density,
      'part_type': partType,
      'problem_zones': problemZones.toJson(),
    };
  }
}

class ProblemZones {
  final bool hasBaldSpots;
  final String? baldType;
  final double topAreaPercentage;
  final String? spotSizeCategory;
  final List<String> spotLocations;

  ProblemZones({
    required this.hasBaldSpots,
    this.baldType,
    required this.topAreaPercentage,
    this.spotSizeCategory,
    required this.spotLocations,
  });

  factory ProblemZones.fromJson(Map<String, dynamic> json) {
    return ProblemZones(
      hasBaldSpots: json['has_bald_spots'] ?? false,
      baldType: json['bald_type'],
      topAreaPercentage: (json['top_area_percentage'] ?? 0).toDouble(),
      spotSizeCategory: json['spot_size_category'],
      spotLocations: List<String>.from(json['spot_locations'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'has_bald_spots': hasBaldSpots,
      'bald_type': baldType,
      'top_area_percentage': topAreaPercentage,
      'spot_size_category': spotSizeCategory,
      'spot_locations': spotLocations,
    };
  }

  String getFormattedDescription() {
    if (!hasBaldSpots) return 'Отсутствуют';

    final List<String> parts = [];
    if (baldType != null) parts.add(baldType!);
    if (topAreaPercentage > 0)
      parts.add('${topAreaPercentage.toStringAsFixed(1)}% площади');
    if (spotSizeCategory != null) parts.add('размер $spotSizeCategory');
    if (spotLocations.isNotEmpty)
      parts.add('локации: ${spotLocations.join(", ")}');

    return parts.join(', ');
  }
}

class Recommendation {
  final String technique;
  final String materials;
  final String schemeDescription;
  final String instructions;
  final String careRecommendations;
  final String fullResponse;

  Recommendation({
    required this.technique,
    required this.materials,
    required this.schemeDescription,
    required this.instructions,
    required this.careRecommendations,
    required this.fullResponse,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      technique: json['technique'] ?? 'не указана',
      materials: json['materials'] ?? 'не указаны',
      schemeDescription: json['scheme_description'] ?? 'не указана',
      instructions: json['instructions'] ?? 'не указана',
      careRecommendations: json['care_recommendations'] ?? 'не указаны',
      fullResponse: json['full_response'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'technique': technique,
      'materials': materials,
      'scheme_description': schemeDescription,
      'instructions': instructions,
      'care_recommendations': careRecommendations,
      'full_response': fullResponse,
    };
  }
}

// Расширения для форматирования
extension PartTypeExtension on String {
  String getDisplayName() {
    switch (this) {
      case 'прямой':
        return 'Прямой пробор';
      case 'сбоку':
        return 'Боковой пробор';
      case 'зигзаг':
        return 'Зигзагообразный пробор';
      case 'полукруг':
        return 'Полукруглый пробор';
      case 'облысение':
        return 'Пробор отсутствует (облысение)';
      default:
        return this;
    }
  }
}

extension DensityExtension on String {
  String getDisplayName() {
    switch (this) {
      case 'густые':
        return 'Густые';
      case 'средние':
        return 'Средние';
      case 'редкие':
        return 'Редкие';
      case 'облысение':
        return 'Облысение';
      default:
        return this;
    }
  }
}

extension TextureExtension on String {
  String getDisplayName() {
    switch (this) {
      case 'прямые':
        return 'Прямые';
      case 'волнистые':
        return 'Волнистые';
      case 'кудрявые':
        return 'Кудрявые';
      case 'курчавые':
        return 'Курчавые';
      case 'облысение':
        return 'Облысение';
      default:
        return this;
    }
  }
}
