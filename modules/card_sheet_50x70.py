import os
import math
from PIL import Image, ImageDraw

DPI_DEFAULT = 400
# 1 inch = 25.4 mm
# 500 mm * 400 / 25.4 = 7874.0157 -> 7874 px
# 700 mm * 400 / 25.4 = 11023.622 -> 11024 px
PAPER_W_MM = 500
PAPER_H_MM = 700

# Card dimensions (Portrait / Dikey)
CARD_W_MM = 59.0
CARD_H_MM = 86.0

# Bleed / Taşma payı: 5mm on each side (top, bottom, left, right)
BLEED_MM = 5.0
CELL_W_MM = CARD_W_MM + 2 * BLEED_MM  # 69.0 mm
CELL_H_MM = CARD_H_MM + 2 * BLEED_MM  # 96.0 mm

COLS = 7
ROWS = 7
TOTAL_SLOTS = COLS * ROWS  # 49

DEFAULT_CARD_BACK_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "img", "card_back_50x70.jpg")


def mm_to_px(mm, dpi=DPI_DEFAULT):
    return round(mm * dpi / 25.4)


def calculate_grid_positions_50x70(dpi=DPI_DEFAULT, grid_order="col_first"):
    canvas_w = mm_to_px(PAPER_W_MM, dpi)
    canvas_h = mm_to_px(PAPER_H_MM, dpi)

    cell_w = mm_to_px(CELL_W_MM, dpi)
    cell_h = mm_to_px(CELL_H_MM, dpi)

    # Exact alignment to cover the base card in genisletilmis kart (937 x 1297):
    # Base card sits at: x=88, y=82, w=760, h=1129 in 937x1297.
    # At 400 DPI (1087 x 1512 cell), with 1px bleed overlap:
    # card_x_offset = 101, card_y_offset = 95, card_w = 884, card_h = 1318
    card_x_offset = round(cell_w * 101 / 1087)
    card_y_offset = round(cell_h * 95 / 1512)
    card_w = round(cell_w * 884 / 1087)
    card_h = round(cell_h * 1318 / 1512)

    # 7 * 69mm = 483mm. Remaining width on 500mm = 17mm.
    total_grid_w = COLS * cell_w
    total_grid_h = ROWS * cell_h

    margin_x = max(0, (canvas_w - total_grid_w) // 2)
    margin_y = max(0, (canvas_h - total_grid_h) // 2)

    slots = []
    if grid_order == "col_first":
        for c in range(COLS):
            for r in range(ROWS):
                cx = margin_x + c * cell_w
                cy = margin_y + r * cell_h
                slots.append({
                    "col": c,
                    "row": r,
                    "cell_x": cx,
                    "cell_y": cy,
                    "cell_w": cell_w,
                    "cell_h": cell_h,
                    "card_x": cx + card_x_offset,
                    "card_y": cy + card_y_offset,
                    "card_w": card_w,
                    "card_h": card_h,
                    "card_x_offset": card_x_offset,
                    "card_y_offset": card_y_offset
                })
    else:  # row_first
        for r in range(ROWS):
            for c in range(COLS):
                cx = margin_x + c * cell_w
                cy = margin_y + r * cell_h
                slots.append({
                    "col": c,
                    "row": r,
                    "cell_x": cx,
                    "cell_y": cy,
                    "cell_w": cell_w,
                    "cell_h": cell_h,
                    "card_x": cx + card_x_offset,
                    "card_y": cy + card_y_offset,
                    "card_w": card_w,
                    "card_h": card_h,
                    "card_x_offset": card_x_offset,
                    "card_y_offset": card_y_offset
                })

    return {
        "canvas_w": canvas_w,
        "canvas_h": canvas_h,
        "cell_w": cell_w,
        "cell_h": cell_h,
        "card_w": card_w,
        "card_h": card_h,
        "card_x_offset": card_x_offset,
        "card_y_offset": card_y_offset,
        "bleed_x": card_x_offset,
        "bleed_y": card_y_offset,
        "margin_x": margin_x,
        "margin_y": margin_y,
        "slots": slots
    }


def prepare_card_image(image_path, target_w, target_h, rotation="none"):
    """
    Loads, scales and optionally rotates a card image directly to target_w x target_h
    using high quality Lanczos resampling without any edge cropping.
    """
    with Image.open(image_path) as src_img:
        img = src_img.convert("RGB")
        w, h = img.size

        if rotation == "ccw90":
            img = img.transpose(Image.Transpose.ROTATE_90)
        elif rotation == "cw90":
            img = img.transpose(Image.Transpose.ROTATE_270)
        elif rotation == "auto":
            # If user uploaded a horizontal image but target is vertical
            if w > h and target_h > target_w:
                img = img.transpose(Image.Transpose.ROTATE_90)

        # High quality Lanczos resize directly to exact card dimensions
        card_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        return card_resized


def prepare_card_back(card_back_path, target_w, target_h):
    """
    Prepares the card back background image to fill target_w x target_h (the 69x96mm cell).
    """
    p = card_back_path if card_back_path and os.path.isfile(card_back_path) else DEFAULT_CARD_BACK_PATH
    if os.path.isfile(p):
        with Image.open(p) as src:
            img = src.convert("RGB")
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        # Fallback dark luxury purple-black background
        return Image.new("RGB", (target_w, target_h), (20, 18, 28))


def draw_crop_marks(draw, card_x, card_y, card_w, card_h, style="corners"):
    if style == "none":
        return

    line_color = (0, 0, 0)
    line_width = 3

    if style == "border":
        draw.rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            outline=line_color,
            width=line_width
        )
    elif style == "corners":
        mark_len = 25
        mark_gap = 6

        # Top-left
        draw.line([(card_x - mark_gap - mark_len, card_y), (card_x - mark_gap, card_y)], fill=line_color, width=line_width)
        draw.line([(card_x, card_y - mark_gap - mark_len), (card_x, card_y - mark_gap)], fill=line_color, width=line_width)

        # Top-right
        draw.line([(card_x + card_w + mark_gap, card_y), (card_x + card_w + mark_gap + mark_len, card_y)], fill=line_color, width=line_width)
        draw.line([(card_x + card_w, card_y - mark_gap - mark_len), (card_x + card_w, card_y - mark_gap)], fill=line_color, width=line_width)

        # Bottom-left
        draw.line([(card_x - mark_gap - mark_len, card_y + card_h), (card_x - mark_gap, card_y + card_h)], fill=line_color, width=line_width)
        draw.line([(card_x, card_y + card_h + mark_gap), (card_x, card_y + card_h + mark_gap + mark_len)], fill=line_color, width=line_width)

        # Bottom-right
        draw.line([(card_x + card_w + mark_gap, card_y + card_h), (card_x + card_w + mark_gap + mark_len, card_y + card_h)], fill=line_color, width=line_width)
        draw.line([(card_x + card_w, card_y + card_h + mark_gap), (card_x + card_w, card_y + card_h + mark_gap + mark_len)], fill=line_color, width=line_width)


def draw_guillotine_marks(draw, layout, canvas_w, canvas_h):
    """
    Draws guillotine cut guide marks in the outer margins of the 50x70 cm sheet.
    Marks are aligned precisely to the original 5.9cm x 8.6cm cards:
    - 14 vertical cut lines (left and right edges of each of the 7 card columns)
    - 14 horizontal cut lines (top and bottom edges of each of the 7 card rows)
    """
    line_color = (0, 0, 0)
    line_width = 3

    margin_x = layout["margin_x"]
    margin_y = layout["margin_y"]
    cell_w = layout["cell_w"]
    cell_h = layout["cell_h"]
    card_w = layout["card_w"]
    card_h = layout["card_h"]
    bleed_x = layout["bleed_x"]
    bleed_y = layout["bleed_y"]
    total_grid_w = COLS * cell_w
    total_grid_h = ROWS * cell_h

    # 14 vertical cut lines (left and right edges of 7 card columns)
    for c in range(COLS):
        cell_x = margin_x + c * cell_w
        x_left = cell_x + bleed_x
        x_right = cell_x + bleed_x + card_w

        for x in [x_left, x_right]:
            # Top margin mark: from paper top (y=0) to grid top (margin_y)
            draw.line([(x, 0), (x, margin_y)], fill=line_color, width=line_width)
            # Bottom margin mark: from grid bottom to paper bottom (canvas_h)
            draw.line([(x, margin_y + total_grid_h), (x, canvas_h)], fill=line_color, width=line_width)

    # 14 horizontal cut lines (top and bottom edges of 7 card rows)
    for r in range(ROWS):
        cell_y = margin_y + r * cell_h
        y_top = cell_y + bleed_y
        y_bottom = cell_y + bleed_y + card_h

        for y in [y_top, y_bottom]:
            # Left margin mark: from paper left (x=0) to grid left (margin_x)
            draw.line([(0, y), (margin_x, y)], fill=line_color, width=line_width)
            # Right margin mark: from grid right to paper right (canvas_w)
            draw.line([(margin_x + total_grid_w, y), (canvas_w, y)], fill=line_color, width=line_width)


def generate_card_sheet_50x70(
    image_paths,
    output_path,
    dpi=DPI_DEFAULT,
    fill_mode="uploaded_only",
    rotation="none",
    empty_color="card_back",
    crop_marks="guillotine",
    export_format="png",
    grid_order="col_first",
    card_back_path=None
):
    """
    Generates a 50x70 cm sheet with 49 card slots (7x7) at 400 DPI.
    Each slot has a 6.9x9.6cm cell with card back bleed, and a centered 5.9x8.6cm card.
    Outer margins contain guillotine cut guide marks at cell junctions.
    """
    layout = calculate_grid_positions_50x70(dpi=dpi, grid_order=grid_order)
    canvas_w = layout["canvas_w"]
    canvas_h = layout["canvas_h"]
    cell_w = layout["cell_w"]
    cell_h = layout["cell_h"]
    card_w = layout["card_w"]
    card_h = layout["card_h"]
    slots = layout["slots"]

    # White 50x70 cm paper background
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Prepare card back background for cells
    card_back_img = prepare_card_back(card_back_path, cell_w, cell_h)

    num_images = len(image_paths)

    for i in range(TOTAL_SLOTS):
        slot = slots[i]
        has_card = False
        img_path = None

        if fill_mode == "repeat" and num_images > 0:
            img_path = image_paths[i % num_images]
            has_card = True
        elif fill_mode == "uploaded_only" and i < num_images:
            img_path = image_paths[i]
            has_card = True

        # 1. Draw cell background (6.9 x 9.6 cm)
        if empty_color == "card_back" or has_card:
            canvas.paste(card_back_img, (slot["cell_x"], slot["cell_y"]))
        elif empty_color == "black":
            draw.rectangle(
                [slot["cell_x"], slot["cell_y"], slot["cell_x"] + cell_w, slot["cell_y"] + cell_h],
                fill=(18, 18, 18)
            )
        elif empty_color == "gray":
            draw.rectangle(
                [slot["cell_x"], slot["cell_y"], slot["cell_x"] + cell_w, slot["cell_y"] + cell_h],
                fill=(40, 44, 52)
            )
        else:  # white
            draw.rectangle(
                [slot["cell_x"], slot["cell_y"], slot["cell_x"] + cell_w, slot["cell_y"] + cell_h],
                fill=(255, 255, 255),
                outline=(220, 220, 220),
                width=1
            )

        # 2. Draw card centered inside cell (5.9 x 8.6 cm)
        if has_card and img_path and os.path.isfile(img_path):
            card_img = prepare_card_image(img_path, card_w, card_h, rotation=rotation)
            canvas.paste(card_img, (slot["card_x"], slot["card_y"]))
        else:
            # If empty slot, draw inner slot outline placeholder only for solid dark colors
            if empty_color in ["black", "gray"]:
                draw.rectangle(
                    [slot["card_x"], slot["card_y"], slot["card_x"] + card_w, slot["card_y"] + card_h],
                    outline=(80, 80, 80),
                    width=2
                )

    # 3. Outer margin guillotine cut guide marks (en dış hatlarda, kartların üstünden asla geçmez)
    if crop_marks != "none":
        draw_guillotine_marks(draw, layout, canvas_w, canvas_h)

    # Save output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if export_format == "pdf":
        import fitz
        doc = fitz.open()
        # 500 mm x 700 mm in points (72 pt / inch): 500 / 25.4 * 72 = 1417.32 pt, 700 / 25.4 * 72 = 1984.25 pt
        pt_w = 500.0 * 72.0 / 25.4
        pt_h = 700.0 * 72.0 / 25.4
        page = doc.new_page(width=pt_w, height=pt_h)

        temp_img_path = output_path + ".tmp.jpg"
        canvas.save(temp_img_path, "JPEG", quality=95, dpi=(dpi, dpi))
        rect = fitz.Rect(0, 0, pt_w, pt_h)
        page.insert_image(rect, filename=temp_img_path)
        doc.save(output_path)
        doc.close()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
    elif export_format in ["jpg", "jpeg"]:
        canvas.save(output_path, "JPEG", quality=100, dpi=(dpi, dpi), subsampling=0)
    else:
        # Default PNG with exact 400 DPI pHYs chunk
        canvas.save(output_path, "PNG", dpi=(dpi, dpi))

    return output_path
