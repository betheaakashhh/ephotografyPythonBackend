PRESETS = {
    "passport": {
        "width_mm": 35,
        "height_mm": 45,
        "face_ratio": 0.75,# face height = 75% of photo
        "canvas_w": 1772,
        "canvas_h": 1181,
        "photo_w": 413, "photo_h": 531,
    },
    "visa": {
        "width_mm": 51,
        "height_mm": 51,
        "face_ratio": 0.70,
        "canvas_w": 1772,
        "canvas_h": 1181,
        "photo_w": 606, "photo_h": 606,
    }
}
def mm_to_px(mm: int, dpi=300):
    return int((mm / 25.4) * dpi)
