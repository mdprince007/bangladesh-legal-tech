import os
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageOps, ImageFilter
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

class DeedCVPipeline:
    """
    Advanced Document Vision Pipeline for Historical Bangladeshi Land Deeds.
    Implements:
    - Image Quality Analysis (Resolution, DPI, Blur, Contrast, Illumination, Skew)
    - Page Rectification & Deskew
    - Multi-pass Image Enhancement (preserves original as source of truth)
    - Document Layout Analysis (Stamp, Parties, Land Schedule, Boundaries, Signatures)
    - Handwritten Text Line Segmentation via Horizontal Projection Profiles & Valley Detection
    """

    @staticmethod
    def analyze_image_quality(img_path_or_array: Any) -> Dict[str, Any]:
        """
        Calculates optical quality metrics:
        - resolution (w, h)
        - estimated DPI (assuming 8.5 x 14 in legal paper)
        - blur score (Laplacian variance: <100 blurry, 100-500 moderate, >500 sharp)
        - contrast (std dev of luminance)
        - brightness (mean luminance)
        - skew angle (degrees)
        - ink fading ratio
        - quality level & warnings
        """
        if isinstance(img_path_or_array, str):
            img = cv2.imread(img_path_or_array)
        else:
            img = img_path_or_array

        if img is None:
            return {
                "quality_level": "ERROR",
                "overall_score": 0,
                "warnings": ["চিত্র লোড করা সম্ভব হয়নি"]
            }

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        # 1. Resolution & DPI estimation
        est_dpi_w = round(w / 8.5, 1)
        est_dpi_h = round(h / 14.0, 1)
        avg_dpi = int((est_dpi_w + est_dpi_h) / 2)

        # 2. Blur / Sharpness via Laplacian Variance
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # 3. Contrast (Luminance Standard Deviation)
        contrast_std = float(np.std(gray))

        # 4. Brightness (Mean Luminance)
        brightness_mean = float(np.mean(gray))

        # 5. Skew Angle Detection
        skew_angle = DeedCVPipeline._detect_skew_angle(gray)

        # 6. Ink Fading Metric (ratio of low-contrast ink pixels)
        ink_mask = gray < (brightness_mean - 15)
        ink_pixel_ratio = float(np.sum(ink_mask) / (w * h) * 100)

        # 7. Quality Categorization & Warnings
        warnings = []
        score = 85

        if avg_dpi < 120:
            score -= 30
            warnings.append(f"নিম্ন রেজোলিউশন (আনুমানিক {avg_dpi} DPI): দলিলের ক্ষুদ্র হস্তলিপি পড়ার জন্য ন্যূনতম ৩০০ DPI স্ক্যান সুপারিশ করা হয়।")
        elif avg_dpi < 200:
            score -= 15
            warnings.append(f"মাঝারি রেজোলিউশন ({avg_dpi} DPI): কিছু যুক্তাক্ষর ও কার অস্পষ্ট হতে পারে।")

        if laplacian_var < 80:
            score -= 25
            warnings.append("অতিরিক্ত অস্পষ্টতা (Blur): ক্যামেরার ফোকাস বা মোশন ব্লারের কারণে হস্তলিপি ঝাপসা।")
        elif laplacian_var < 200:
            score -= 10
            warnings.append("হালকা অস্পষ্টতা: কালির ধার কিছুটা ছড়িয়ে গেছে।")

        if contrast_std < 25:
            score -= 20
            warnings.append("স্বল্প কনট্রাস্ট: কালির রং ফিকে হয়ে কাগজের রঙের সাথে মিশে গেছে।")

        if abs(skew_angle) > 3.0:
            warnings.append(f"দলিলটি {abs(skew_angle):.1f}° কোণে বাঁকা (Tilted); স্বয়ংক্রিয় রেকটিফিকেশন সক্রিয় করা হয়েছে।")

        if ink_pixel_ratio < 2.0:
            warnings.append("অত্যন্ত হালকা কালি (Faded Ink): পাতলা লেখার কিছু অংশ অপাঠ্য হতে পারে।")

        overall_score = max(10, min(100, score))
        if overall_score >= 75:
            quality_level = "EXCELLENT" if overall_score >= 90 else "ADEQUATE"
            quality_badge_bn = "সন্তোষজনক" if overall_score >= 90 else "ব্যবহারযোগ্য"
        elif overall_score >= 50:
            quality_level = "DEGRADED"
            quality_badge_bn = "মাঝারি অস্পষ্ট"
        else:
            quality_level = "CRITICALLY_LOW"
            quality_badge_bn = "অতিরিক্ত ক্ষয়প্রাপ্ত / নিম্নমান"

        return {
            "width": w,
            "height": h,
            "estimated_dpi": avg_dpi,
            "blur_metric": round(laplacian_var, 1),
            "contrast_std": round(contrast_std, 1),
            "brightness_mean": round(brightness_mean, 1),
            "skew_angle": round(skew_angle, 2),
            "ink_pixel_ratio": round(ink_pixel_ratio, 2),
            "overall_score": overall_score,
            "quality_level": quality_level,
            "quality_badge_bn": quality_badge_bn,
            "warnings": warnings,
            "recommendation": "আইনি কার্যক্রমে শতভাগ নিশ্চয়তার জন্য সাব-রেজিস্ট্রারের মূল বালাম বই এবং ৩০০ DPI ফ্ল্যাটবেড স্ক্যানার দিয়ে স্ক্যান করা কপি ব্যবহার করুন।" if overall_score < 75 else "নথির অপটিক্যাল মান প্রাথমিক ডিজিটাল নিরীক্ষার জন্য উপযুক্ত।"
        }

    @staticmethod
    def _detect_skew_angle(gray: np.ndarray) -> float:
        """Detects page tilt/skew angle in degrees using Hough Lines on horizontal strokes."""
        try:
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=gray.shape[1] // 4, maxLineGap=20)
            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines:
                    coords = line[0] if len(line.shape) > 1 else line
                    x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    if abs(angle) < 40:
                        angles.append(angle)
                if angles:
                    return float(np.median(angles))
        except Exception:
            pass
        return 0.0

    @staticmethod
    def rectify_and_deskew(img: np.ndarray) -> Tuple[np.ndarray, float]:
        """Rectifies and deskews image if tilt angle is greater than 0.5 degrees."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        angle = DeedCVPipeline._detect_skew_angle(gray)

        if abs(angle) > 0.5 and abs(angle) < 30.0:
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rectified = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rectified, angle
        return img, 0.0

    @staticmethod
    def generate_preprocessing_variants(crop: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Generates multi-pass preprocessing variants without aggressive binarization.
        Preserves thin handwritten strokes, matra, and ligatures.
        """
        if len(crop.shape) == 2:
            gray = crop
            bgr = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        else:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            bgr = crop

        # 1. Original (Source of Truth)
        variants = {"original": bgr}

        # 2. Grayscale Background Normalized (morphological rolling ball division)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        bg = cv2.morphologyEx(gray, cv2.MORPH_DILATE, kernel)
        diff = cv2.absdiff(gray, bg)
        norm_gray = 255 - diff
        variants["normalized"] = cv2.cvtColor(norm_gray, cv2.COLOR_GRAY2BGR)

        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        clahe_gray = clahe.apply(norm_gray)
        variants["clahe"] = cv2.cvtColor(clahe_gray, cv2.COLOR_GRAY2BGR)

        # 4. Bilateral Filter (Noise reduction preserving thin stroke edges)
        bilateral = cv2.bilateralFilter(clahe_gray, d=7, sigmaColor=50, sigmaSpace=50)
        variants["bilateral"] = cv2.cvtColor(bilateral, cv2.COLOR_GRAY2BGR)

        # 5. Mild Stroke Sharpening (Unsharp mask for faint handwriting)
        blurred = cv2.GaussianBlur(clahe_gray, (0, 0), sigmaX=1.5)
        sharpened = cv2.addWeighted(clahe_gray, 1.4, blurred, -0.4, 0)
        variants["sharpened"] = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

        return variants

    @staticmethod
    def detect_document_layout_zones(img: np.ndarray) -> List[Dict[str, Any]]:
        """
        Performs Document Layout Analysis classifying semantic zones:
        - ZONE_STAMP_HEADER: Top 0%-25% (Govt emblem, 500 Taka stamp, serial)
        - ZONE_REGISTRATION_METADATA: Top sub-registry office and registry entries
        - ZONE_HANDWRITTEN_PARTIES: Upper body 25%-50% (Sellers, Buyers, Fathers)
        - ZONE_HANDWRITTEN_SCHEDULE: Mid body 50%-72% (Mouza, JL, Khatian, Dag, Area)
        - ZONE_CHOUHADDI_BOUNDARIES: Lower mid 70%-84% (North, South, East, West)
        - ZONE_FINANCIALS_AND_TITLE: 82%-90% (Consideration, prior deed chain)
        - ZONE_SIGNATURES_AND_SEALS: Bottom 88%-100% (Signatures, seals, stamps)
        """
        h, w = img.shape[:2]
        zones = [
            {
                "zone_id": "ZONE_STAMP_HEADER",
                "title_bn": "সরকারি নন-জুডিশিয়াল স্ট্যাম্প ও মনোগ্রাম",
                "type": "printed_stamp",
                "bbox": [0, 0, w, int(h * 0.25)],
                "normalized_bbox": [0.0, 0.0, 1.0, 0.25],
                "description": "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার পাঁচশত টাকার নন-জুডিশিয়াল স্ট্যাম্প ও রাজস্ব সিল।"
            },
            {
                "zone_id": "ZONE_REGISTRATION_METADATA",
                "title_bn": "রেজিস্ট্রেশন অফিস ও বালাম বই পরিচিতি",
                "type": "stamp_and_script",
                "bbox": [int(w * 0.5), int(h * 0.18), w, int(h * 0.28)],
                "normalized_bbox": [0.5, 0.18, 1.0, 0.28],
                "description": "সাব-রেজিস্ট্রি অফিস, বালাম বই ভলিউম নং ও রেজিস্ট্রি ফি।"
            },
            {
                "zone_id": "ZONE_HANDWRITTEN_PARTIES",
                "title_bn": "১ম ও ২য় পক্ষ পরিচিতি (হস্তলিখিত)",
                "type": "handwritten_text",
                "bbox": [int(w * 0.04), int(h * 0.27), int(w * 0.96), int(h * 0.50)],
                "normalized_bbox": [0.04, 0.27, 0.96, 0.50],
                "description": "১ম পক্ষ বিক্রেতাগণ, পিতা, সাং, এবং ২য় পক্ষ ক্রেতা ও পিতার পরিচিতি।"
            },
            {
                "zone_id": "ZONE_HANDWRITTEN_SCHEDULE",
                "title_bn": "সম্পত্তির তফশিল বিবরণী (হস্তলিখিত)",
                "type": "handwritten_text",
                "bbox": [int(w * 0.04), int(h * 0.49), int(w * 0.96), int(h * 0.72)],
                "normalized_bbox": [0.04, 0.49, 0.96, 0.72],
                "description": "মৌজা, জে.এল, সি.এস/এস.এ/আর.এস খতিয়ান, সাবেক ও হাল দাগ, জমির শতক ও হিস্যা।"
            },
            {
                "zone_id": "ZONE_CHOUHADDI_BOUNDARIES",
                "title_bn": "চৌহদ্দি ও চার সীমানা (হস্তলিখিত)",
                "type": "handwritten_text",
                "bbox": [int(w * 0.04), int(h * 0.70), int(w * 0.96), int(h * 0.84)],
                "normalized_bbox": [0.04, 0.70, 0.96, 0.84],
                "description": "উত্তর, দক্ষিণ, পূর্ব ও পশ্চিম পার্শ্বের সীমানা ও রাস্তা/গোপাট বিবরণ।"
            },
            {
                "zone_id": "ZONE_FINANCIALS_AND_TITLE",
                "title_bn": "পণমূল্য ও পূর্বসূত্র বায়া দলিল",
                "type": "handwritten_text",
                "bbox": [int(w * 0.04), int(h * 0.82), int(w * 0.96), int(h * 0.90)],
                "normalized_bbox": [0.04, 0.82, 0.96, 0.90],
                "description": "নগদ পণমূল্য টাকা ও পূর্ববর্তী বায়া দলিল / ওয়ারিশান তথ্য।"
            },
            {
                "zone_id": "ZONE_SIGNATURES_AND_SEALS",
                "title_bn": "টিপসহি, স্বাক্ষর ও শনাক্তকারী",
                "type": "signatures_and_seals",
                "bbox": [int(w * 0.04), int(h * 0.88), int(w * 0.96), h],
                "normalized_bbox": [0.04, 0.88, 0.96, 1.0],
                "description": "পক্ষগণের টিপসই, স্বাক্ষর, দলিল লেখক ও শনাক্তকারী এডভোকেটের সিল।"
            }
        ]
        return zones

    @staticmethod
    def segment_handwritten_lines(img: np.ndarray, y_start_ratio: float = 0.27, y_end_ratio: float = 0.88) -> List[Dict[str, Any]]:
        """
        Segments the dense handwritten body into individual horizontal text lines
        using horizontal projection profiles with Gaussian smoothing and valley detection.
        Preserves coordinates [x1, y1, x2, y2] traceable back to original image.
        """
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        y1_abs = int(h * y_start_ratio)
        y2_abs = int(h * y_end_ratio)
        body = gray[y1_abs:y2_abs, :]

        # Normalize illumination and apply soft adaptive threshold
        blurred = cv2.GaussianBlur(body, (3, 3), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6)

        # Horizontal projection profile: sum across columns
        proj = np.sum(thresh, axis=1).astype(float)
        smoothed = gaussian_filter1d(proj, sigma=3.0)

        # Find line peaks (baselines / shirorekha)
        peaks, _ = find_peaks(smoothed, distance=14, prominence=2500)
        
        if len(peaks) == 0:
            # Fallback uniform slicing if profile has no distinct peaks
            step = 28
            peaks = list(range(14, len(smoothed) - 14, step))

        line_crops = []
        for i, p in enumerate(peaks):
            prev_p = peaks[i - 1] if i > 0 else max(0, p - 14)
            next_p = peaks[i + 1] if i < len(peaks) - 1 else min(len(smoothed) - 1, p + 14)

            top = int(p - (p - prev_p) * 0.55)
            bottom = int(p + (next_p - p) * 0.55)

            line_y1 = max(0, y1_abs + top)
            line_y2 = min(h, y1_abs + bottom)
            line_h = line_y2 - line_y1

            if line_h >= 10:
                pos_pct = line_y1 / h
                if pos_pct < 0.50:
                    zone = "ZONE_HANDWRITTEN_PARTIES"
                elif pos_pct < 0.72:
                    zone = "ZONE_HANDWRITTEN_SCHEDULE"
                elif pos_pct < 0.85:
                    zone = "ZONE_CHOUHADDI_BOUNDARIES"
                else:
                    zone = "ZONE_FINANCIALS_AND_TITLE"

                line_crops.append({
                    "line_index": i + 1,
                    "zone": zone,
                    "bbox": [int(w * 0.04), line_y1, int(w * 0.96), line_y2],
                    "normalized_bbox": [0.04, round(line_y1 / h, 4), 0.96, round(line_y2 / h, 4)],
                    "height_px": line_h,
                    "center_y": y1_abs + p
                })

        return line_crops

deed_cv_pipeline = DeedCVPipeline()
