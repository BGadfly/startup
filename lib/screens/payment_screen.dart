import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/subscription_plan.dart';
import '../services/api_service.dart';
import 'package:url_launcher/url_launcher.dart';

class PaymentScreen extends StatefulWidget {
  final SubscriptionPlan plan;

  const PaymentScreen({super.key, required this.plan});

  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  final TextEditingController _promoController = TextEditingController();
  bool _isProcessing = false;
  Map<String, dynamic>? _paymentData;

  Future<void> _createPayment() async {
    setState(() {
      _isProcessing = true;
    });

    final apiService = Provider.of<ApiService>(context, listen: false);
    final paymentData = await apiService.createPayment(
      planId: widget.plan.planId,
      promoCode: _promoController.text.isNotEmpty ? _promoController.text : null,
    );

    setState(() {
      _paymentData = paymentData;
      _isProcessing = false;
    });

    if (paymentData != null && paymentData['confirmation_url'] != null) {
      _showPaymentDialog(paymentData['confirmation_url']);
    }
  }

  void _showPaymentDialog(String url) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Оплата'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Для завершения оплаты перейдите по ссылке:'),
            const SizedBox(height: 16),
            Text(
              url,
              style: const TextStyle(color: Colors.blue),
              textAlign: TextAlign.center,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Закрыть'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (await canLaunchUrl(Uri.parse(url))) {
                await launchUrl(Uri.parse(url));
              }
            },
            child: const Text('Перейти к оплате'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Оформление подписки'),
        backgroundColor: Colors.pink,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Text(
                      widget.plan.name,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${widget.plan.price} ₽',
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.pink,
                      ),
                    ),
                    Text('на ${widget.plan.durationDays} дней'),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Что вы получите:',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    ...widget.plan.features.map((feature) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        children: [
                          const Icon(Icons.check, size: 20, color: Colors.green),
                          const SizedBox(width: 8),
                          Text(feature),
                        ],
                      ),
                    )),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Промокод',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _promoController,
                      decoration: const InputDecoration(
                        hintText: 'Введите промокод',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isProcessing ? null : _createPayment,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.pink,
                  foregroundColor: Colors.white,
                ),
                child: _isProcessing
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Оплатить'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}