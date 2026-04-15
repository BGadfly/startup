// lib/services/api_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/hair_analysis.dart'; // Изменен импорт
import '../models/subscription_plan.dart';
import 'package:http_parser/http_parser.dart';
import 'package:mime/mime.dart';
import 'package:path/path.dart' as path;

class ApiService extends ChangeNotifier {
  final String userId;

  // Динамическое определение baseUrl для разных платформ
  String get baseUrl {
    if (kIsWeb) {
      return 'http://localhost:5000'; // Для веб
    } else if (Platform.isAndroid) {
      return 'http://192.168.0.74:5000'; // Android - порт 5000 (Flask по умолчанию)
    } else if (Platform.isIOS) {
      return 'http://localhost:5000'; // iOS эмулятор
    } else {
      return 'http://192.168.0.74:5000'; // Для реального устройства
    }
  }

  bool _isLoading = false;
  String? _errorMessage;

  ApiService({required this.userId});

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String? error) {
    _errorMessage = error;
    notifyListeners();
  }

  void clearError() {
    _setError(null);
  }

  /// Анализ волос по 3 фотографиям
  Future<AnalysisResult?> analyzeHair({
    required List<File> photos,
    required String comment,
    VoidCallback? onProgress,
  }) async {
    if (photos.length != 3) {
      _setError('Необходимо загрузить ровно 3 фотографии');
      return null;
    }

    _setLoading(true);
    _setError(null);

    if (onProgress != null) onProgress();

    try {
      // Создаем multipart запрос
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze'),
      );

      // Добавляем фотографии с правильными ключами (photo1, photo2, photo3)
      final List<String> photoKeys = ['photo1', 'photo2', 'photo3'];

      for (var i = 0; i < photos.length && i < photoKeys.length; i++) {
        final file = photos[i];

        // Проверяем существование файла
        if (!await file.exists()) {
          throw Exception('Файл ${file.path} не существует');
        }

        var stream = http.ByteStream(file.openRead());
        var length = await file.length();

        // Определяем MIME тип автоматически
        final mimeType = lookupMimeType(file.path) ?? 'image/jpeg';
        final mimeSplit = mimeType.split('/');

        // Получаем расширение файла
        final fileExtension = path.extension(file.path);

        var multipartFile = http.MultipartFile(
          photoKeys[i], // Используем правильные ключи для бэкенда
          stream,
          length,
          filename: 'photo_${i + 1}$fileExtension',
          contentType: MediaType(mimeSplit[0], mimeSplit[1]),
        );

        request.files.add(multipartFile);
        print('Добавлен файл ${photoKeys[i]}: ${file.path}');
      }

      // Добавляем комментарий
      request.fields['comment'] = comment;
      request.fields['user_id'] =
          userId; // Добавляем ID пользователя для логирования

      print('Отправка запроса на $baseUrl/analyze');
      print('Файлов: ${request.files.length}, Комментарий: $comment');

      // Отправляем запрос с таймаутом
      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 120), // Увеличенный таймаут для обработки фото
        onTimeout: () {
          throw Exception('Превышено время ожидания ответа от сервера');
        },
      );

      // Получаем ответ
      final responseBody = await streamedResponse.stream.bytesToString();

      _setLoading(false);

      if (streamedResponse.statusCode == 200) {
        try {
          final Map<String, dynamic> jsonData = jsonDecode(responseBody);

          if (jsonData['success'] == true) {
            print('Анализ успешно завершен');
            return AnalysisResult.fromJson(jsonData);
          } else {
            _setError(jsonData['error'] ?? 'Неизвестная ошибка при анализе');
            return null;
          }
        } catch (e) {
          print('Ошибка парсинга JSON: $e');
          print('Ответ сервера: $responseBody');
          _setError('Ошибка обработки ответа сервера: $e');
          return null;
        }
      } else {
        _setError(
          'Ошибка сервера: ${streamedResponse.statusCode}\n$responseBody',
        );
        return null;
      }
    } catch (e) {
      _setLoading(false);
      _setError('Ошибка соединения: $e');
      print('Ошибка при анализе: $e');
      return null;
    }
  }

  /// Получение планов подписки
  Future<List<SubscriptionPlan>> getSubscriptionPlans() async {
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/subscription/plans'),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => SubscriptionPlan.fromJson(json)).toList();
      } else {
        print('Error fetching plans: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching plans: $e');
    }
    return [];
  }

  /// Создание платежа
  Future<Map<String, dynamic>?> createPayment({
    required String planId,
    String? promoCode,
  }) async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/subscription/create-payment'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'plan_id': planId,
              'user_id': userId,
              'promo_code': promoCode,
            }),
          )
          .timeout(const Duration(seconds: 30));

      _setLoading(false);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data;
        } else {
          _setError(data['error'] ?? 'Ошибка создания платежа');
        }
      } else {
        _setError('Ошибка сервера: ${response.statusCode}');
      }
    } catch (e) {
      _setLoading(false);
      _setError('Ошибка соединения: $e');
      print('Error creating payment: $e');
    }
    return null;
  }

  /// Получение статуса подписки
  Future<SubscriptionStatus> getSubscriptionStatus() async {
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/subscription/status/$userId'),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return SubscriptionStatus.fromJson(data);
      } else {
        print('Error fetching subscription status: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching subscription status: $e');
    }

    return SubscriptionStatus(
      hasSubscription: false,
      extensionsUsed: 0,
      extensionsLimit: 0,
      remainingExtensions: 0,
      planName: null,
      expiresAt: null,
      message: 'Не удалось получить статус подписки',
    );
  }

  /// Использование одной расшифровки
  Future<Map<String, dynamic>?> useExtension() async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/subscription/use-extension/$userId'),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 10));

      _setLoading(false);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        _setError(error['detail'] ?? 'Ошибка использования расшифровки');
      }
    } catch (e) {
      _setLoading(false);
      _setError('Ошибка соединения: $e');
      print('Error using extension: $e');
    }
    return null;
  }

  /// Проверка здоровья сервера
  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/health'),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      print('Health check failed: $e');
      return false;
    }
  }

  /// Отмена подписки
  Future<Map<String, dynamic>?> cancelSubscription() async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/subscription/cancel/$userId'),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 10));

      _setLoading(false);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        _setError(error['detail'] ?? 'Ошибка отмены подписки');
      }
    } catch (e) {
      _setLoading(false);
      _setError('Ошибка соединения: $e');
      print('Error canceling subscription: $e');
    }
    return null;
  }
}

/// Модель статуса подписки (дополненная)
class SubscriptionStatus {
  final bool hasSubscription;
  final int extensionsUsed;
  final int extensionsLimit;
  final int remainingExtensions;
  final String? planName;
  final DateTime? expiresAt;
  final String message;

  SubscriptionStatus({
    required this.hasSubscription,
    required this.extensionsUsed,
    required this.extensionsLimit,
    required this.remainingExtensions,
    this.planName,
    this.expiresAt,
    required this.message,
  });

  factory SubscriptionStatus.fromJson(Map<String, dynamic> json) {
    return SubscriptionStatus(
      hasSubscription: json['has_subscription'] ?? false,
      extensionsUsed: json['extensions_used'] ?? 0,
      extensionsLimit: json['extensions_limit'] ?? 0,
      remainingExtensions: json['remaining_extensions'] ?? 0,
      planName: json['plan_name'],
      expiresAt: json['expires_at'] != null
          ? DateTime.parse(json['expires_at'])
          : null,
      message: json['message'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'has_subscription': hasSubscription,
      'extensions_used': extensionsUsed,
      'extensions_limit': extensionsLimit,
      'remaining_extensions': remainingExtensions,
      'plan_name': planName,
      'expires_at': expiresAt?.toIso8601String(),
      'message': message,
    };
  }
}
