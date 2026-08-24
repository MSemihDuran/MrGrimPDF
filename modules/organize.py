import os
import fitz
import zipfile

def merge_pdfs(file_paths, output_path):
    merged_doc = fitz.open()
    try:
        for fpath in file_paths:
            if not os.path.exists(fpath):
                continue
            with fitz.open(fpath) as doc:
                if doc.is_encrypted and not doc.authenticate(""):
                    raise ValueError(f"Password-protected PDF cannot be merged: {os.path.basename(fpath)}")
                merged_doc.insert_pdf(doc)
        if not len(merged_doc):
            raise ValueError("No readable PDF pages were provided.")
        merged_doc.save(output_path, garbage=4, deflate=True)
    finally:
        merged_doc.close()
    return output_path

def split_pdf(file_path, output_dir, mode='all', ranges_str='', extract_pages=None):
    doc = fitz.open(file_path)
    total_pages = len(doc)
    created_files = []
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    if mode == 'all':
        for i in range(total_pages):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            out_file = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
            new_doc.save(out_file)
            new_doc.close()
            created_files.append(out_file)
    
    elif mode == 'extract':
        if not extract_pages:
            extract_pages = [1]
        new_doc = fitz.open()
        for p in extract_pages:
            idx = int(p) - 1
            if 0 <= idx < total_pages:
                new_doc.insert_pdf(doc, from_page=idx, to_page=idx)
        out_file = os.path.join(output_dir, f"{base_name}_extracted.pdf")
        new_doc.save(out_file)
        new_doc.close()
        doc.close()
        return out_file

    elif mode == 'ranges':
        parts = [p.strip() for p in ranges_str.split(',') if p.strip()]
        for idx, part in enumerate(parts):
            new_doc = fitz.open()
            if '-' in part:
                start, end = part.split('-', 1)
                start_idx = max(0, int(start.strip()) - 1)
                end_idx = min(total_pages - 1, int(end.strip()) - 1)
                if start_idx <= end_idx:
                    new_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx)
            else:
                p_idx = int(part) - 1
                if 0 <= p_idx < total_pages:
                    new_doc.insert_pdf(doc, from_page=p_idx, to_page=p_idx)
            
            if len(new_doc) > 0:
                out_file = os.path.join(output_dir, f"{base_name}_part_{idx+1}.pdf")
                new_doc.save(out_file)
                new_doc.close()
                created_files.append(out_file)

    doc.close()

    if len(created_files) == 1:
        return created_files[0]
    elif len(created_files) > 1:
        zip_path = os.path.join(output_dir, f"{base_name}_split.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in created_files:
                zf.write(f, os.path.basename(f))
        return zip_path
    else:
        raise ValueError("No pages were extracted or split.")

def remove_pages(file_path, output_path, pages_to_remove):
    doc = fitz.open(file_path)
    total_pages = len(doc)
    remove_indices = sorted({int(p) - 1 for p in pages_to_remove if 0 < int(p) <= total_pages}, reverse=True)
    if len(remove_indices) >= total_pages:
        doc.close()
        raise ValueError("A PDF must retain at least one page.")
    
    for idx in remove_indices:
        doc.delete_page(idx)
        
    doc.save(output_path)
    doc.close()
    return output_path

def reorder_pages(file_path, output_path, new_order):
    doc = fitz.open(file_path)
    total_pages = len(doc)
    new_doc = fitz.open()
    
    seen = set()
    for p in new_order:
        idx = int(p) - 1
        if 0 <= idx < total_pages and idx not in seen:
            new_doc.insert_pdf(doc, from_page=idx, to_page=idx)
            seen.add(idx)
    if not len(new_doc):
        new_doc.close()
        doc.close()
        raise ValueError("Select at least one valid page to organize.")
    new_doc.save(output_path, garbage=4, deflate=True)
    new_doc.close()
    doc.close()
    return output_path

def rotate_pages(file_path, output_path, rotation_map, global_angle=0, pages_to_remove=None):
    doc = fitz.open(file_path)
    for i, page in enumerate(doc):
        p_num = i + 1
        angle_to_add = 0
        if rotation_map and str(p_num) in rotation_map:
            angle_to_add = int(rotation_map[str(p_num)])
        elif rotation_map and p_num in rotation_map:
            angle_to_add = int(rotation_map[p_num])
        elif global_angle:
            angle_to_add = int(global_angle)
            
        if angle_to_add:
            current_rot = page.rotation
            page.set_rotation((current_rot + angle_to_add) % 360)
    if pages_to_remove:
        remove_indices = sorted({int(p) - 1 for p in pages_to_remove if 0 < int(p) <= len(doc)}, reverse=True)
        if len(remove_indices) >= len(doc):
            doc.close()
            raise ValueError("A PDF must retain at least one page.")
        for idx in remove_indices:
            doc.delete_page(idx)
    doc.save(output_path)
    doc.close()
    return output_path

def crop_pdf(file_path, output_path, left_pct=0, top_pct=0, right_pct=0, bottom_pct=0):
    values = [float(left_pct), float(top_pct), float(right_pct), float(bottom_pct)]
    if any(value < 0 or value >= 100 for value in values):
        raise ValueError("Crop values must be between 0 and 99.9 percent.")
    if values[0] + values[2] >= 100 or values[1] + values[3] >= 100:
        raise ValueError("Opposite crop values must total less than 100 percent.")
    doc = fitz.open(file_path)
    for page in doc:
        rect = page.rect
        w = rect.width
        h = rect.height
        new_rect = fitz.Rect(
            rect.x0 + (left_pct / 100.0) * w,
            rect.y0 + (top_pct / 100.0) * h,
            rect.x1 - (right_pct / 100.0) * w,
            rect.y1 - (bottom_pct / 100.0) * h
        )
        page.set_cropbox(new_rect)
    doc.save(output_path)
    doc.close()
    return output_path
