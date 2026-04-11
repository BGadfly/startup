// lib/services/api_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/analysis_result.dart';
import '../models/subscription_plan.dart';
import 'package:http_parser/http_parser.dart';
import 'package:mime/mime.dart';

class ApiService extends ChangeNotifier {
  final String userId;
  String get baseUrl {
    if (Platform.isAndroid) {
      return 'http://192.168.0.74:8000';  // Android эмулятор
    } else if (Platform.isIOS) {
      return 'http://localhost:8000'; // iOS эмулятор
    } else {
      return 'http://192.168.0.74:8000'; // Для реального устройства
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

  Future<AnalysisResult?> analyzeHair({
    required List<File> photos,
    required String comment,
  }) async {
    if (photos.length != 3) {
      _setError('Необходимо загрузить ровно 3 фотографии');
      return null;
    }

    _setLoading(true);
    _setError(null);

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze'),
      );

      for (var i = 0; i < photos.length; i++) {
        final file = photos[i];

        var stream = http.ByteStream(file.openRead());
        var length = await file.length();

        // 🔥 Определяем MIME тип автоматически
        final mimeType = lookupMimeType(file.path) ?? 'image/jpeg';
        final mimeSplit = mimeType.split('/');

        var multipartFile = http.MultipartFile(
          'photos',
          stream,
          length,
          filename: file.path.split('/').last,
          contentType: MediaType(mimeSplit[0], mimeSplit[1]),
        );

        request.files.add(multipartFile);
      }

      request.fields['comment'] = comment;

      var response = await request.send();
      var responseBody = await response.stream.bytesToString();

      _setLoading(false);

      if (response.statusCode == 200) {
        return AnalysisResult.fromJson(jsonDecode(responseBody));
      } else {
        _setError('Ошибка: ${response.statusCode} | $responseBody');
        return null;
      }
    } catch (e) {
      _setLoading(false);
      _setError('Ошибка соединения: $e');
      return null;
    }
  }

  Future<List<SubscriptionPlan>> getSubscriptionPlans() async {
    try {
      var response = await http.get(
        Uri.parse('$baseUrl/subscription/plans'),
      );

      if (response.statusCode == 200) {
        List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => SubscriptionPlan.fromJson(json)).toList();
      }
    } catch (e) {
      print('Error fetching plans: $e');
    }
    return [];
  }

  Future<Map<String, dynamic>?> createPayment({
    required String planId,
    String? promoCode,
  }) async {
    _setLoading(true);

    try {
      var response = await http.post(
        Uri.parse('$baseUrl/subscription/create-payment'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'plan_id': planId,
          'user_id': userId,
          'promo_code': promoCode,
        }),
      );

      _setLoading(false);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      _setLoading(false);
      _setError('Ошибка создания платежа: $e');
    }
    return null;
  }

  Future<SubscriptionStatus> getSubscriptionStatus() async {
    try {
      var response = await http.get(
        Uri.parse('$baseUrl/subscription/status/$userId'),
      );

      if (response.statusCode == 200) {
        return SubscriptionStatus.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      print('Error fetching subscription status: $e');
    }
    return SubscriptionStatus(
      hasSubscription: false,
      extensionsUsed: 0,
      extensionsLimit: 0,
      message: 'Не удалось получить статус',
    );
  }

  Future<Map<String, dynamic>?> useExtension() async {
    try {
      var response = await http.post(
        Uri.parse('$baseUrl/subscription/use-extension/$userId'),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Error using extension: $e');
    }
    return null;
  }


}

