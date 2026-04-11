class SubscriptionPlan {
  final String planId;
  final String name;
  final int price;
  final int durationDays;
  final List<String> features;
  final int extensionLimit;

  SubscriptionPlan({
    required this.planId,
    required this.name,
    required this.price,
    required this.durationDays,
    required this.features,
    required this.extensionLimit,
  });

  factory SubscriptionPlan.fromJson(Map<String, dynamic> json) {
    return SubscriptionPlan(
      planId: json['plan_id'],
      name: json['name'],
      price: json['price'],
      durationDays: json['duration_days'],
      features: List<String>.from(json['features']),
      extensionLimit: json['extension_limit'],
    );
  }
}

class SubscriptionStatus {
  final bool hasSubscription;
  final String? subscriptionId;
  final Map<String, dynamic>? plan;
  final String? expiresAt;
  final int? daysLeft;
  final int extensionsUsed;
  final int extensionsLimit;
  final String? message;

  SubscriptionStatus({
    required this.hasSubscription,
    this.subscriptionId,
    this.plan,
    this.expiresAt,
    this.daysLeft,
    required this.extensionsUsed,
    required this.extensionsLimit,
    this.message,
  });

  factory SubscriptionStatus.fromJson(Map<String, dynamic> json) {
    return SubscriptionStatus(
      hasSubscription: json['has_subscription'] ?? false,
      subscriptionId: json['subscription_id'],
      plan: json['plan'],
      expiresAt: json['expires_at'],
      daysLeft: json['days_left'],
      extensionsUsed: json['extensions_used'] ?? 0,
      extensionsLimit: json['extensions_limit'] ?? 0,
      message: json['message'],
    );
  }
}