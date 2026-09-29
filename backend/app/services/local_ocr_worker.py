"""
Out-of-process local OCR (EasyOCR, Bengali + English).

Run as:  python -m app.services.local_ocr_worker <image_path> [<image_path> ...]
Prints one JSON object: {"pages": [{"lines": [{"text", "conf", "bbox"}]}]}

It runs in its own process because PyTorch can crash the whole interpreter (segfault) when the
machine is short on memory; a crash here must never take the web server down with it.
Local OCR is only used as weak corroboration: on real handwritten deeds it is not accurate enough
to be trusted on its own.
"""
import json
import os
import sys

MAX_SIDE = int(os.getenv("LOCAL_OCR_MAX_SIDE", "1100"))
CANVAS = int(os.getenv("LOCAL_OCR_CANVAS", "768"))


def main(paths):
    import warnings
    warnings.filterwarnings("ignore")
    import cv2
    import easyocr

    reader = easyocr.Reader(["bn", "en"], gpu=False, verbose=False)
    pages = []
    for path in paths:
        img = cv2.imread(path)
        if img is None:
            pages.append({"lines": [], "error": "unreadable image"})
            continue
        h, w = img.shape[:2]
        scale = min(1.0, MAX_SIDE / float(max(h, w)))
        if scale < 1.0:
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        lines = []
        for box, text, conf in reader.readtext(img, canvas_size=CANVAS, batch_size=1):
            xs = [p[0] / scale for p in box]
            ys = [p[1] / scale for p in box]
            lines.append({
                "text": text,
                "conf": round(float(conf), 3),
                "bbox": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
            })
        pages.append({"lines": lines})
    sys.stdout.write(json.dumps({"pages": pages}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
