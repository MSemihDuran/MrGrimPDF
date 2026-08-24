import os
import tempfile
import fitz
from PIL import Image

def hex_to_rgb_float(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    if len(hex_str) != 6:
        return (0.0, 0.0, 0.0)
    return tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def add_watermark(file_path, output_path, wm_type='text', text='CONFIDENTIAL',
                  image_path=None, opacity=0.35, rotation=45, position='center',
                  font_size=48, color='#E11D48', layer='over'):
    doc = fitz.open(file_path)
    rgb_color = hex_to_rgb_float(color)
    prepared_image_path = image_path
    temp_image_path = None
    if wm_type == 'image' and image_path and os.path.exists(image_path) and float(opacity) < 1:
        # PyMuPDF's image insertion has no opacity parameter. Prepare a
        # transparent PNG once, then reuse it on every page.
        with Image.open(image_path).convert('RGBA') as source:
            alpha = source.getchannel('A').point(lambda value: int(value * max(0.0, min(float(opacity), 1.0))))
            source.putalpha(alpha)
            handle = tempfile.NamedTemporaryFile(prefix='mrgrimpdf_wm_', suffix='.png', delete=False)
            temp_image_path = handle.name
            handle.close()
            source.save(temp_image_path, 'PNG')
        prepared_image_path = temp_image_path
    
    for page in doc:
        rect = page.rect
        w = rect.width
        h = rect.height
        
        if wm_type == 'text':
            cx, cy = w / 2, h / 2
            if 'top' in position:
                cy = h * 0.2
            elif 'bottom' in position:
                cy = h * 0.8
                
            if 'left' in position:
                cx = w * 0.25
            elif 'right' in position:
                cx = w * 0.75
                
            point = fitz.Point(cx, cy)
            morph_param = (point, fitz.Matrix(rotation)) if rotation else None
            
            page.insert_text(
                point,
                text,
                fontsize=font_size,
                color=rgb_color,
                morph=morph_param,
                render_mode=0,
                overlay=True if layer == 'over' else False,
                fill_opacity=max(0.0, min(float(opacity), 1.0)),
            )
            
        elif wm_type == 'image' and prepared_image_path and os.path.exists(prepared_image_path):
            img_doc = fitz.open(prepared_image_path)
            img_rect = img_doc[0].rect
            aspect = img_rect.width / img_rect.height if img_rect.height else 1
            
            target_w = w * 0.4
            target_h = target_w / aspect
            
            x0 = (w - target_w) / 2
            y0 = (h - target_h) / 2
            
            if 'top' in position:
                y0 = h * 0.05
            elif 'bottom' in position:
                y0 = h * 0.95 - target_h
                
            if 'left' in position:
                x0 = w * 0.05
            elif 'right' in position:
                x0 = w * 0.95 - target_w
                
            target_rect = fitz.Rect(x0, y0, x0 + target_w, y0 + target_h)
            page.insert_image(
                target_rect,
                filename=prepared_image_path,
                overlay=True if layer == 'over' else False,
            )
            img_doc.close()
            
    try:
        doc.save(output_path, garbage=4, deflate=True)
    finally:
        doc.close()
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
    return output_path

def add_page_numbers(file_path, output_path, format_str='{page} / {total}',
                     position='bottom-center', font_size=10, start_num=1,
                     color='#4B5563', margin_pt=30):
    doc = fitz.open(file_path)
    total_pages = len(doc)
    rgb_color = hex_to_rgb_float(color)
    
    for i, page in enumerate(doc):
        current_num = start_num + i
        label = format_str.replace('{page}', str(current_num)).replace('{total}', str(total_pages))
        rect = page.rect
        w = rect.width
        h = rect.height
        
        if 'top' in position:
            y = margin_pt + font_size
        else:
            y = h - margin_pt
            
        if 'left' in position:
            x = margin_pt
            align = 0
        elif 'right' in position:
            x = w - margin_pt
            align = 2
        else:
            x = w / 2
            align = 1
            
        text_rect = fitz.Rect(
            margin_pt if align != 2 else w - 200 - margin_pt,
            y - font_size,
            w - margin_pt if align != 0 else margin_pt + 200,
            y + font_size
        )
        
        page.insert_textbox(
            text_rect,
            label,
            fontsize=font_size,
            color=rgb_color,
            align=align,
            fontname="helv"
        )
        
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path

def apply_annotations(file_path, output_path, annotations, overlay_image_path=None, overlay_page=1):
    doc = fitz.open(file_path)
    total_pages = len(doc)
    
    for item in annotations:
        p_num = int(item.get('page', 1)) - 1
        if not (0 <= p_num < total_pages):
            continue
        page = doc[p_num]
        a_type = item.get('type')
        color = hex_to_rgb_float(item.get('color', '#FF0000'))
        
        if a_type == 'text':
            rect = fitz.Rect(item['x'], item['y'], item['x'] + item.get('w', 200), item['y'] + item.get('h', 50))
            page.insert_textbox(rect, item.get('text', ''), fontsize=item.get('fontSize', 14), color=color)
            
        elif a_type == 'rect':
            rect = fitz.Rect(item['x'], item['y'], item['x'] + item['w'], item['y'] + item['h'])
            fill_color = hex_to_rgb_float(item.get('fill', '#FFFFFF')) if item.get('fill') else None
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(color=color, fill=fill_color, width=item.get('strokeWidth', 2))
            shape.commit()
            
        elif a_type == 'freehand':
            points = item.get('points', [])
            if len(points) > 1:
                shape = page.new_shape()
                shape.draw_line(fitz.Point(points[0]['x'], points[0]['y']), fitz.Point(points[1]['x'], points[1]['y']))
                for k in range(1, len(points)-1):
                    shape.draw_line(fitz.Point(points[k]['x'], points[k]['y']), fitz.Point(points[k+1]['x'], points[k+1]['y']))
                shape.finish(color=color, width=item.get('strokeWidth', 2))
                shape.commit()

    if overlay_image_path and os.path.exists(overlay_image_path):
        page_index = int(overlay_page) - 1
        if not 0 <= page_index < total_pages:
            doc.close()
            raise ValueError("The selected annotation page does not exist.")
        # The client canvas has a transparent background; mapping it to the
        # complete PDF page preserves all pen, box and text marks as one overlay.
        page = doc[page_index]
        page.insert_image(page.rect, filename=overlay_image_path, overlay=True, keep_proportion=False)
                
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path
