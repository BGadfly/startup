import 'dart:io';
import 'package:image_picker/image_picker.dart';

class ImagePickerService {
  final ImagePicker _picker = ImagePicker();

  Future<List<File>> pickMultipleImages(int count) async {
    List<File> images = [];

    for (int i = 0; i < count; i++) {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 80,
      );

      if (image != null) {
        images.add(File(image.path));
      } else {
        break;
      }
    }

    return images;
  }

  Future<File?> pickSingleImage() async {
    final XFile? image = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 80,
    );

    if (image != null) {
      return File(image.path);
    }
    return null;
  }
}