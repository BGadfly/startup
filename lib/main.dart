import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/home_screen.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final prefs = await SharedPreferences.getInstance();
  final userId = prefs.getString('user_id') ?? _generateUserId();
  await prefs.setString('user_id', userId);

  runApp(MyApp(userId: userId));
}

String _generateUserId() {
  return 'user_${DateTime.now().millisecondsSinceEpoch}';
}

class MyApp extends StatelessWidget {
  final String userId;

  const MyApp({super.key, required this.userId});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ApiService(userId: userId)),
      ],
      child: MaterialApp(
        title: 'Hair Extension',
        theme: ThemeData(
          primarySwatch: Colors.pink,
          useMaterial3: true,
          appBarTheme: const AppBarTheme(
            backgroundColor: Colors.pink,
            foregroundColor: Colors.white,
          ),
        ),
        home: HomeScreen(userId: userId),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}