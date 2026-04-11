import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/subscription_plan.dart';

class ProfileScreen extends StatefulWidget {
  final String userId;

  const ProfileScreen({super.key, required this.userId});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _isLoading = true;
  SubscriptionStatus? _subscription;

  @override
  void initState() {
    super.initState();
    _loadSubscription();
  }

  Future<void> _loadSubscription() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final status = await apiService.getSubscriptionStatus();
    setState(() {
      _subscription = status;
      _isLoading = false;
    });
  }

  Future<void> _useExtension() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final result = await apiService.useExtension();

    if (result != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['success'] ? 'Услуга использована' : 'Ошибка')),
      );
      _loadSubscription();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Профиль'),
        backgroundColor: Colors.pink,
      ),
      body: RefreshIndicator(
        onRefresh: _loadSubscription,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    const CircleAvatar(
                      radius: 40,
                      backgroundColor: Colors.pink,
                      child: Icon(Icons.person, size: 40, color: Colors.white),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'ID: ${widget.userId}',
                      style: const TextStyle(fontFamily: 'monospace'),
                    ),
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
                      'Моя подписка',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const Divider(),

                    if (_subscription?.hasSubscription == true) ...[
                      Text(
                        _subscription?.plan?['name'] ?? 'Активна',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text('Дней осталось: ${_subscription?.daysLeft ?? 0}'),
                      Text('Использовано наращиваний: ${_subscription?.extensionsUsed ?? 0}/${_subscription?.extensionsLimit ?? 0}'),
                      const SizedBox(height: 16),

                      LinearProgressIndicator(
                        value: (_subscription?.extensionsUsed ?? 0) / (_subscription?.extensionsLimit ?? 1),
                        backgroundColor: Colors.grey.shade200,
                        color: Colors.pink,
                      ),

                      const SizedBox(height: 16),

                      if ((_subscription?.extensionsUsed ?? 0) < (_subscription?.extensionsLimit ?? 0))
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: _useExtension,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.pink,
                              foregroundColor: Colors.white,
                            ),
                            child: const Text('Использовать наращивание'),
                          ),
                        ),
                    ] else ...[
                      const Icon(Icons.warning_amber, size: 48, color: Colors.orange),
                      const SizedBox(height: 8),
                      Text(
                        _subscription?.message ?? 'Нет активной подписки',
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.pushNamed(context, '/subscription');
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.pink,
                            foregroundColor: Colors.white,
                          ),
                          child: const Text('Оформить подписку'),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}