import os
import fitz
from PIL import Image, ImageDraw

DPI_DEFAULT = 400
MM_TO_INCH = 1.0 / 25.4

def mm_to_pixels(mm_val, dpi=DPI_DEFAULT):
    return round(mm_val * MM_TO_INCH * dpi)

A3_WIDTH_MM = 297.0
A3_HEIGHT_MM = 420.0

CARD_WIDTH_MM = 86.0
CARD_HEIGHT_MM = 59.0

GRID_COLS = 3
GRID_ROWS = 6
TOTAL_SLOTS = 18

def calculate_grid_positions(dpi=DPI_DEFAULT, gap_mm=2.5, grid_order="col_first"):
    canvas_w = mm_to_pixels(A3_WIDTH_MM, dpi)
    canvas_h = mm_to_pixels(A3_HEIGHT_MM, dpi)

    card_w = mm_to_pixels(CARD_WIDTH_MM, dpi)
    card_h = mm_to_pixels(CARD_HEIGHT_MM, dpi)
    gap_x = mm_to_pixels(gap_mm, dpi)
    gap_y = mm_to_pixels(gap_mm, dpi)

    total_grid_w = (GRID_COLS * card_w) + ((GRID_COLS - 1) * gap_x)
    total_grid_h = (GRID_ROWS * card_h) + ((GRID_ROWS - 1) * gap_y)

    margin_x = (canvas_w - total_grid_w) // 2
    margin_y = (canvas_h - total_grid_h) // 2

    slots = []
    if grid_order == "col_first":
        # Fill downwards column-by-column (matches user reference image: Slot 1, 2, 3 in Col 1)
        for col in range(GRID_COLS):
            for row in range(GRID_ROWS):
                x = margin_x + col * (card_w + gap_x)
                y = margin_y + row * (card_h + gap_y)
                slots.append({
                    "col": col,
                    "row": row,
                    "x": x,
                    "y": y,
                    "w": card_w,
                    "h": card_h
                })
    else:
        # Fill left-to-right row-by-row
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = margin_x + col * (card_w + gap_x)
                y = margin_y + row * (card_h + gap_y)
                slots.append({
                    "col": col,
                    "row": row,
                    "x": x,
                    "y": y,
                    "w": card_w,
                    "h": card_h
                })

    return {
        "canvas_w": canvas_w,
        "canvas_h": canvas_h,
        "card_w": card_w,
        "card_h": card_h,
        "gap_x": gap_x,
        "gap_y": gap_y,
        "margin_x": margin_x,
        "margin_y": margin_y,
        "slots": slots
    }

def prepare_card_image(image_path, target_w, target_h, rotation="ccw90"):
    with Image.open(image_path) as src_img:
        img = src_img.convert("RGB")
        w, h = img.size

        if rotation == "ccw90":
            img = img.transpose(Image.Transpose.ROTATE_90)
        elif rotation == "cw90":
            img = img.transpose(Image.Transpose.ROTATE_270)
        elif rotation == "auto":
            if h > w:
                img = img.transpose(Image.Transpose.ROTATE_90)

        if img.size != (target_w, target_h):
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        return img

def draw_crop_marks(draw, x, y, w, h, mark_len=30, mark_gap=6, outline_color=(0, 0, 0), line_width=2):
    draw.line([(x - mark_gap - mark_len, y), (x - mark_gap, y)], fill=outline_color, width=line_width)
    draw.line([(x, y - mark_gap - mark_len), (x, y - mark_gap)], fill=outline_color, width=line_width)

    draw.line([(x + w + mark_gap, y), (x + w + mark_gap + mark_len, y)], fill=outline_color, width=line_width)
    draw.line([(x + w, y - mark_gap - mark_len), (x + w, y - mark_gap)], fill=outline_color, width=line_width)

    draw.line([(x - mark_gap - mark_len, y + h), (x - mark_gap, y + h)], fill=outline_color, width=line_width)
    draw.line([(x, y + h + mark_gap), (x, y + h + mark_gap + mark_len)], fill=outline_color, width=line_width)

    draw.line([(x + w + mark_gap, y + h), (x + w + mark_gap + mark_len, y + h)], fill=outline_color, width=line_width)
    draw.line([(x + w, y + h + mark_gap), (x + w, y + h + mark_gap + mark_len)], fill=outline_color, width=line_width)

def generate_card_sheet(
    image_paths,
    output_path,
    dpi=DPI_DEFAULT,
    gap_mm=2.5,
    fill_mode="uploaded_only",
    rotation="ccw90",
    empty_color="black",
    crop_marks="none",
    export_format="png",
    grid_order="col_first"
):
    layout = calculate_grid_positions(dpi=dpi, gap_mm=gap_mm, grid_order=grid_order)
    canvas_w = layout["canvas_w"]
    canvas_h = layout["canvas_h"]
    card_w = layout["card_w"]
    card_h = layout["card_h"]
    slots = layout["slots"]

    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    valid_paths = [p for p in (image_paths or []) if p and os.path.exists(p)]
    slot_assignments = [None] * TOTAL_SLOTS

    if valid_paths:
        if fill_mode == "repeat":
            for idx in range(TOTAL_SLOTS):
                slot_assignments[idx] = valid_paths[idx % len(valid_paths)]
        else:
            for idx in range(min(len(valid_paths), TOTAL_SLOTS)):
                slot_assignments[idx] = valid_paths[idx]

    empty_fills = {
        "black": (18, 18, 18),
        "gray": (40, 44, 52),
        "white": (255, 255, 255)
    }
    empty_fill_color = empty_fills.get(empty_color, (18, 18, 18))

    for idx, slot in enumerate(slots):
        x = slot["x"]
        y = slot["y"]
        card_path = slot_assignments[idx]

        if card_path:
            try:
                card_img = prepare_card_image(card_path, card_w, card_h, rotation=rotation)
                canvas.paste(card_img, (x, y))
            except Exception:
                draw.rectangle([x, y, x + card_w, y + card_h], fill=empty_fill_color, outline=(120, 120, 120), width=1)
        else:
            outline_c = (80, 80, 80) if empty_color != "white" else (200, 200, 200)
            draw.rectangle([x, y, x + card_w, y + card_h], fill=empty_fill_color, outline=outline_c, width=1)

        if crop_marks == "corners":
            draw_crop_marks(draw, x, y, card_w, card_h, mark_len=round(25 * (dpi / 400)), mark_gap=round(5 * (dpi / 400)), outline_color=(0, 0, 0), line_width=2)
        elif crop_marks == "border":
            draw.rectangle([x, y, x + card_w, y + card_h], outline=(0, 0, 0), width=2)

    fmt = str(export_format).lower().strip()
    target_ext = os.path.splitext(output_path)[1].lower()

    if fmt == "pdf" or target_ext == ".pdf":
        temp_img_path = output_path + ".tmp.png"
        try:
            canvas.save(temp_img_path, format="PNG", dpi=(dpi, dpi))
            doc = fitz.open()
            page = doc.new_page(width=841.89, height=1190.55)
            page.insert_image(fitz.Rect(0, 0, 841.89, 1190.55), filename=temp_img_path)
            doc.save(output_path, deflate=True)
            doc.close()
        finally:
            if os.path.exists(temp_img_path):
                try:
                    os.remove(temp_img_path)
                except Exception:
                    pass

    elif fmt in ["jpeg", "jpg"] or target_ext in [".jpeg", ".jpg"]:
        canvas.save(
            output_path,
            format="JPEG",
            dpi=(dpi, dpi),
            quality=100,
            subsampling=0
        )
    else:
        canvas.save(
            output_path,
            format="PNG",
            dpi=(dpi, dpi),
            optimize=False
        )

    return output_path
