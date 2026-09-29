import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

class DeedImageService:
    @staticmethod
    def enhance_deed_image(input_path: str, output_path: str) -> str:
        """
        Enhances faded, degraded, handwritten historical deed scans.
        Stretches dynamic contrast to wash out yellowed/browned paper and darkens faded pen strokes.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        try:
            with Image.open(input_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Grayscale
                gray = ImageOps.grayscale(img)
                arr = np.array(gray, dtype=np.float32)

                # Percentile stretching (2% to 98%) to eliminate background paper haze
                p_low = np.percentile(arr, 2)
                p_high = np.percentile(arr, 98)
                if p_high > p_low:
                    arr = np.clip((arr - p_low) * (255.0 / (p_high - p_low)), 0, 255)
                stretched = Image.fromarray(arr.astype(np.uint8))

                # Enhance contrast
                enhancer = ImageEnhance.Contrast(stretched)
                contrasted = enhancer.enhance(1.6)

                # Sharpen faint handwritten ink strokes
                sharpened = contrasted.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

                sharpened.save(output_path, format='JPEG', quality=90)
                return output_path
        except Exception:
            import shutil
            shutil.copyfile(input_path, output_path)
            return output_path

deed_image_service = DeedImageService()
