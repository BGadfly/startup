import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/image_picker_service.dart';
import '../screens/analysis_result_screen.dart';

class AnalysisScreen extends StatefulWidget {
  const AnalysisScreen({super.key});

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  final ImagePickerService _pickerService = ImagePickerService();
  final TextEditingController _commentController = TextEditingController();

  List<File> _selectedPhotos = [];
  bool _isAnalyzing = false;

  Future<void> _pickPhotos() async {
    final photos = await _pickerService.pickMultipleImages(3);
    if (photos.isNotEmpty) {
      setState(() {
        _selectedPhotos = photos;
      });
    }
  }

  Future<void> _analyze() async {
    if (_selectedPhotos.length != 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Выберите 3 фотографии')),
      );
      return;
    }

    if (_commentController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Введите комментарий')),
      );
      return;
    }

    setState(() {
      _isAnalyzing = true;
    });

    final apiService = Provider.of<ApiService>(context, listen: false);
    final result = await apiService.analyzeHair(
      photos: _selectedPhotos,
      comment: _commentController.text,
    );

    setState(() {
      _isAnalyzing = false;
    });

    if (result != null && mounted) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => AnalysisResultScreen(result: result),
        ),
      );
    } else if (apiService.errorMessage != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(apiService.errorMessage!)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Анализ волос'),
        backgroundColor: Colors.pink,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.pink.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  const Text(
                    'Для точного подбора загрузите 3 фотографии:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text('• Вид спереди\n• Вид сбоку\n• Вид сзади'),
                ],
              ),
            ),

            const SizedBox(height: 24),

            const Text(
              'Фотографии',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),

            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
              ),
              itemCount: 3,
              itemBuilder: (context, index) {
                if (index < _selectedPhotos.length) {
                  return GestureDetector(
                    onTap: () => _showImagePreview(_selectedPhotos[index]),
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                        image: DecorationImage(
                          image: FileImage(_selectedPhotos[index]),
                          fit: BoxFit.cover,
                        ),
                      ),
                      child: Align(
                        alignment: Alignment.topRight,
                        child: IconButton(
                          icon: const Icon(Icons.close, color: Colors.white),
                          onPressed: () {
                            setState(() {
                              _selectedPhotos.removeAt(index);
                            });
                          },
                        ),
                      ),
                    ),
                  );
                } else {
                  return GestureDetector(
                    onTap: _pickPhotos,
                    child: Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey, width: 2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Center(
                        child: Icon(Icons.add_photo_alternate, size: 32),
                      ),
                    ),
                  );
                }
              },
            ),

            const SizedBox(height: 24),

            TextField(
              controller: _commentController,
              decoration: const InputDecoration(
                labelText: 'Комментарий к заказу',
                border: OutlineInputBorder(),
                hintText: 'Например: хочу объемное наращивание',
              ),
              maxLines: 3,
            ),

            const SizedBox(height: 24),

            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isAnalyzing ? null : _analyze,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.pink,
                  foregroundColor: Colors.white,
                ),
                child: _isAnalyzing
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Проанализировать'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showImagePreview(File image) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        child: GestureDetector(
          onTap: () => Navigator.pop(context),
          child: Image.file(image),
        ),
      ),
    );
  }
}