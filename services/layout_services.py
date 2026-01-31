from PIL import Image


def apply_print_layout(
    subject: Image.Image,
    output_path: str,
    bg_color=(255, 255, 255),
    copies=6,
    canvas_w=1772,
    canvas_h=1181,
    photo_w=413,   # 35mm @300dpi
    photo_h=531    # 45mm @300dpi
):
    subject = subject.convert("RGBA")

    # resize subject to passport photo size
    subject = subject.resize((photo_w, photo_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (canvas_w, canvas_h), bg_color + (255,))

    if copies == 1:
        x = (canvas_w - photo_w) // 2
        y = (canvas_h - photo_h) // 2
        canvas.paste(subject, (x, y), subject)
    else:
        grid_layout(canvas, subject, copies, photo_w, photo_h)

    canvas.info["dpi"] = (300, 300)

    canvas.convert("RGB").save(
        output_path,
        "JPEG",
        quality=95,
        dpi=(300, 300)
    )


def grid_layout(canvas, photo, copies, photo_w, photo_h):
    layouts = {
        4: (2, 2),
        6: (3, 2),
        8: (4, 2)
    }

    cols, rows = layouts.get(copies, (3, 2))

    margin_x = 50
    margin_y = 50

    spacing_x = (canvas.width - cols * photo_w) // (cols + 1)
    spacing_y = (canvas.height - rows * photo_h) // (rows + 1)

    for row in range(rows):
        for col in range(cols):
            if row * cols + col >= copies:
                break

            x = spacing_x + col * (photo_w + spacing_x)
            y = spacing_y + row * (photo_h + spacing_y)

            canvas.paste(photo, (x, y), photo)


def validate_print_ready(img: Image.Image):
    dpi = img.info.get("dpi", (72, 72))
    if dpi[0] < 300 or dpi[1] < 300:
        raise ValueError("Image DPI too low for print (must be 300 DPI)")
    
