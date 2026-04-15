// models/hair_analysis.dart

class AnalysisResult {
  final String comment;
  final Map<String, PhotoAnalysis> photosAnalysis; // front, side, top
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
}

class PhotoAnalysis {
  final String viewType; // front, side, top
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
}

class ProblemZones {
  final bool hasBaldSpots;
  final String? baldType; // "залысины", "лысина", "местное выпадение"
  final double topAreaPercentage; // процент площади сверху
  final String? spotSizeCategory; // "до 5см", "5-10см", "больше 10см"
  final List<String> spotLocations; // локации проблем

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
}

// Вспомогательные функции для форматирования
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

extension BaldTypeExtension on String {
  String getDisplayName() {
    switch (this) {
      case 'залысины':
        return 'Залысины';
      case 'лысина':
        return 'Лысина';
      case 'местное выпадение':
        return 'Местное выпадение';
      default:
        return this;
    }
  }
}

// Функция для отправки запроса к бэкенду
class HairAnalysisService {
  static const String baseUrl =
      'YOUR_PYTHON_BACKEND_URL'; // Замените на ваш URL

  Future<AnalysisResult> analyzeHair({
    required String photo1Base64, // анфас
    required String photo2Base64, // профиль
    required String photo3Base64, // сверху
    String comment = '',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/analyze'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'photo1': photo1Base64,
          'photo2': photo2Base64,
          'photo3': photo3Base64,
          'comment': comment,
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        return AnalysisResult.fromJson(data);
      } else {
        return AnalysisResult(
          comment: comment,
          photosAnalysis: {},
          aggregated: AggregatedData(
            texture: 'не определено',
            density: 'не определено',
            partType: 'прямой',
            problemZones: ProblemZones(
              hasBaldSpots: false,
              topAreaPercentage: 0,
              spotLocations: [],
            ),
          ),
          problemZones: ProblemZones(
            hasBaldSpots: false,
            topAreaPercentage: 0,
            spotLocations: [],
          ),
          recommendation: Recommendation(
            technique: 'Ошибка',
            materials: 'Не удалось получить рекомендацию',
            schemeDescription: '',
            instructions: '',
            careRecommendations: '',
            fullResponse: '',
          ),
          success: false,
          error: 'Ошибка сервера: ${response.statusCode}',
        );
      }
    } catch (e) {
      return AnalysisResult(
        comment: comment,
        photosAnalysis: {},
        aggregated: AggregatedData(
          texture: 'не определено',
          density: 'не определено',
          partType: 'прямой',
          problemZones: ProblemZones(
            hasBaldSpots: false,
            topAreaPercentage: 0,
            spotLocations: [],
          ),
        ),
        problemZones: ProblemZones(
          hasBaldSpots: false,
          topAreaPercentage: 0,
          spotLocations: [],
        ),
        recommendation: Recommendation(
          technique: 'Ошибка',
          materials: 'Не удалось получить рекомендацию',
          schemeDescription: '',
          instructions: '',
          careRecommendations: '',
          fullResponse: '',
        ),
        success: false,
        error: 'Ошибка соединения: $e',
      );
    }
  }
}

// Пример использования в Flutter приложении
/*
class HairAnalysisScreen extends StatefulWidget {
  @override
  _HairAnalysisScreenState createState() => _HairAnalysisScreenState();
}

class _HairAnalysisScreenState extends State<HairAnalysisScreen> {
  final HairAnalysisService _service = HairAnalysisService();
  bool _isLoading = false;
  AnalysisResult? _result;

  Future<void> _analyze() async {
    setState(() => _isLoading = true);
    
    // Конвертация файлов в base64
    String photo1Base64 = base64Encode(await _photo1.readAsBytes());
    String photo2Base64 = base64Encode(await _photo2.readAsBytes());
    String photo3Base64 = base64Encode(await _photo3.readAsBytes());
    
    _result = await _service.analyzeHair(
      photo1Base64: photo1Base64,
      photo2Base64: photo2Base64,
      photo3Base64: photo3Base64,
      comment: _commentController.text,
    );
    
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_result != null && _result!.success) {
      return Column(
        children: [
          // Результаты анализа
          Text('Структура: ${_result!.aggregated.texture.getDisplayName()}'),
          Text('Густота: ${_result!.aggregated.density.getDisplayName()}'),
          Text('Пробор: ${_result!.aggregated.partType.getDisplayName()}'),
          
          // Проблемные зоны
          if (_result!.problemZones.hasBaldSpots)
            Text('Проблемные зоны: ${_result!.problemZones.getFormattedDescription()}'),
          
          // Рекомендация
          Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Рекомендуемая техника:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text(_result!.recommendation.technique),
                  SizedBox(height: 8),
                  Text('Материалы:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text(_result!.recommendation.materials),
                  SizedBox(height: 8),
                  Text('Схема:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text(_result!.recommendation.schemeDescription),
                  SizedBox(height: 8),
                  Text('Инструкция:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text(_result!.recommendation.instructions),
                  SizedBox(height: 8),
                  Text('Уход:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text(_result!.recommendation.careRecommendations),
                ],
              ),
            ),
          ),
        ],
      );
    }
    
    return Container(); // Ваш UI загрузки/ошибки
  }
}
*/
