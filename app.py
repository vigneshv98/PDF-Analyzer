import os
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import fitz  # PyMuPDF
from PIL import Image
import tempfile
import base64
import re
import time
from multiprocessing import Pool, cpu_count

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 650 * 1024 * 1024  # 650MB max upload
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.errorhandler(RequestEntityTooLarge)
def handle_file_size_error(e):
    return jsonify({"error": "File too large. Maximum allowed size is 650MB"}), 413

# KDP trim sizes with page count limits by color option
# Format: trim_size: (width, height, {color_option: (min_pages, max_pages)})
KDP_TRIM_SIZES = {
    # Standard trim sizes
    "5 x 8": (5, 8, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "5.25 x 8": (5.25, 8, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "5.5 x 8.5": (5.5, 8.5, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "6 x 9": (6, 9, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "6.14 x 9.21": (6.14, 9.21, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "6.69 x 9.61": (6.69, 9.61, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "7 x 10": (7, 10, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "7.44 x 9.69": (7.44, 9.69, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "7.5 x 9.25": (7.5, 9.25, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "8 x 10": (8, 10, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "8.25 x 6": (8.25, 6, {
        "black_white": (24, 800),
        "black_cream": (24, 750),
        "standard_color": (72, 600),
        "premium_color": (24, 800)
    }),
    "8.25 x 8.25": (8.25, 8.25, {
        "black_white": (24, 800),
        "black_cream": (24, 750),
        "standard_color": (72, 600),
        "premium_color": (24, 800)
    }),
    "8.5 x 8.5": (8.5, 8.5, {
        "black_white": (24, 590),
        "black_cream": (24, 550),
        "standard_color": (72, 600),
        "premium_color": (24, 590)
    }),
    "8.5 x 11": (8.5, 11, {
        "black_white": (24, 590),
        "black_cream": (24, 550),
        "standard_color": (72, 600),
        "premium_color": (24, 590)
    }),
    "8.25 x 11": (8.25, 11, {
        "black_white": (24, 590),
        "black_cream": (24, 550),
        "standard_color": (72, 600),
        "premium_color": (24, 590)
    }),
    "8.27 x 11.69": (8.27, 11.69, {
        "black_white": (24, 780),
        "black_cream": (24, 730),
        "standard_color": None,  # Not available
        "premium_color": (24, 590)
    }),
    # Japanese trim sizes
    "4.06 x 7.17": (4.06, 7.17, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "4.13 x 6.81": (4.13, 6.81, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "4.41 x 6.85": (4.41, 6.85, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "5 x 7.4": (5, 7.4, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "5.04 x 7.17": (5.04, 7.17, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "5.83 x 8.27": (5.83, 8.27, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "5.98 x 8.58": (5.98, 8.58, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "5.98 x 8.94": (5.98, 8.94, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "7.17 x 10.12": (7.17, 10.12, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "7.17 x 8.11": (7.17, 8.11, {
        "black_white": (24, 828),
        "black_cream": (24, 776),
        "standard_color": (72, 600),
        "premium_color": (24, 828)
    }),
    "8.27 x 10.12": (8.27, 10.12, {
        "black_white": (24, 780),
        "black_cream": (24, 730),
        "standard_color": (72, 600),
        "premium_color": (24, 780)
    })
}

# Hardcover trim sizes (separate from paperback)
KDP_HARDCOVER_TRIM_SIZES = {
    "5.5 x 8.5": (5.5, 8.5, {
        "black_white": (75, 550),
        "black_cream": (75, 550),
        "standard_color": None,  # Not available
        "premium_color": (75, 550)
    }),
    "6 x 9": (6, 9, {
        "black_white": (75, 550),
        "black_cream": (75, 550),
        "standard_color": None,  # Not available
        "premium_color": (75, 550)
    }),
    "6.14 x 9.21": (6.14, 9.21, {
        "black_white": (75, 550),
        "black_cream": (75, 550),
        "standard_color": None,  # Not available
        "premium_color": (75, 550)
    }),
    "7 x 10": (7, 10, {
        "black_white": (75, 550),
        "black_cream": (75, 550),
        "standard_color": None,  # Not available
        "premium_color": (75, 550)
    }),
    "8.25 x 11": (8.25, 11, {
        "black_white": (75, 550),
        "black_cream": (75, 550),
        "standard_color": None,  # Not available
        "premium_color": (75, 550)
    })
}

# Color options with display names
COLOR_OPTIONS = {
    "black_white": "Black ink and white paper",
    "black_cream": "Black ink and cream paper",
    "standard_color": "Standard color ink and white paper",
    "premium_color": "Premium color ink and white paper"
}

# Page count limits by color for custom trim sizes (min_pages, max_pages)
PAGE_COUNT_LIMITS_BY_COLOR = {
    "black_white": (24, 828),
    "black_cream": (24, 776),
    "standard_color": (72, 600),
    "premium_color": (24, 828)
}

def check_color_space(image):
    """Check if an image is in CMYK color space"""
    return image.mode == 'CMYK'

# Helper to process a single page in parallel for CMYK image checks
def process_page(args):
    pdf_path, page_idx = args
    local_results = {"color_space_issues": [], "color_space_images": []}
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_idx]
        image_list = page.get_images(full=True)
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            try:
                with Image.open(tmp_path) as img:
                    if not check_color_space(img):
                        issue = f"Image on page {page_idx+1} (#{img_index+1}) is not in CMYK color space"
                        local_results["color_space_issues"].append(issue)
                        img_copy = img.copy()
                        img_copy.thumbnail((150,150), Image.LANCZOS)
                        buf = io.BytesIO()
                        img_copy.save(buf, format="PNG")
                        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        local_results["color_space_images"].append({
                            "image": b64,
                            "page": page_idx+1,
                            "index": img_index+1,
                            "width": img.width,
                            "height": img.height,
                            "mode": img.mode
                        })
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        doc.close()
    except Exception as e:
        local_results["color_space_issues"].append(f"Error processing page {page_idx+1}: {e}")
    return local_results

def check_pdf_for_kdp(pdf_path, trim_size, book_type="paperback", color_option="black_white", include_bleed=False, custom_width=None, custom_height=None):
    """Check if PDF meets KDP guidelines"""
    start_time = time.time()
    print(f"Starting PDF check for {pdf_path}, trim size: {trim_size}, book type: {book_type}, color: {color_option}, include_bleed: {include_bleed}")
    results = {
        "trim_size_match": False,
        "color_space_issues": [],
        "color_space_images": [],
        "page_count": 0,
        "page_count_valid": False,
        "bleed_issues": [],
        "file_size_mb": 0.0,
        "file_size_issues": [],
        "processing_time": 0.0
    }
    
    # Handle custom trim size (only for paperback)
    if trim_size == 'custom':
        try:
            width = float(custom_width)
            height = float(custom_height)
        except (TypeError, ValueError):
            results["bleed_issues"].append("Invalid custom trim dimensions")
            return results
        # Validate bounds for custom trim
        if not (4 <= width <= 8.5 and 6 <= height <= 11.69):
            results["bleed_issues"].append("Custom trim size out of allowed range")
            return results
        trim_data = (width, height, None)
        # Use same page-count limits by color for custom sizes
        page_limits = PAGE_COUNT_LIMITS_BY_COLOR.get(color_option)
        if page_limits is None:
            results["color_space_issues"].append(f"Invalid color option: {color_option}")
            return results
    else:
        # Select the appropriate trim size data based on book type
        trim_sizes = KDP_TRIM_SIZES if book_type == "paperback" else KDP_HARDCOVER_TRIM_SIZES
        # Check if the trim size is valid for the selected book type
        if trim_size not in trim_sizes:
            results["bleed_issues"].append(f"Selected trim size {trim_size} is not available for {book_type}")
            return results
        # Validate color option availability
        trim_data = trim_sizes[trim_size]
        page_limits = trim_data[2].get(color_option)
        if page_limits is None:
            results["color_space_issues"].append(f"{COLOR_OPTIONS[color_option]} is not available for {trim_size} {book_type}")
            return results
    
    # Open the PDF
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    results["page_count"] = page_count
    
    # Check page count validity
    min_pages, max_pages = page_limits
    if min_pages <= page_count <= max_pages:
        results["page_count_valid"] = True
    else:
        results["bleed_issues"].append(
            f"Page count ({page_count}) is outside the allowed range for {trim_size} with {COLOR_OPTIONS[color_option]} " +
            f"(min: {min_pages}, max: {max_pages})"
        )
    
    # Get dimensions of the first page
    first_page = doc[0]
    width_pt, height_pt = first_page.rect.width, first_page.rect.height
    
    # Convert points to inches (72 points = 1 inch)
    width_in = width_pt / 72
    height_in = height_pt / 72
    
    # Bleed allowances: if bleed included, width uses +0.125", height uses +0.25"
    if include_bleed:
        width_with_bleed = trim_data[0] + 0.125
        height_with_bleed = trim_data[1] + 0.25
    else:
        width_with_bleed = trim_data[0]
        height_with_bleed = trim_data[1]
    
    # Tolerance for dimension comparison (0.05 inch)
    tolerance = 0.05
    # Compare actual dimensions to expected (with or without bleed)
    if abs(width_in - width_with_bleed) <= tolerance and abs(height_in - height_with_bleed) <= tolerance:
        results["trim_size_match"] = True
    elif include_bleed and abs(width_in - trim_data[0]) <= tolerance and abs(height_in - trim_data[1]) <= tolerance:
        # Dimensions match trim but without bleed
        results["trim_size_match"] = True
        results["bleed_issues"].append("PDF dimensions match trim size but doesn't include bleed")
    else:
        # Mismatch
        issue_text = (
            f"PDF dimensions ({width_in:.2f}\" x {height_in:.2f}\") don't match "
            f"expected size ({width_with_bleed:.2f}\" x {height_with_bleed:.2f}\")"
        )
        results["bleed_issues"].append(issue_text)
    
    # Parallel CMYK image checks
    if color_option in ["standard_color", "premium_color"]:
        pages_to_check = list(range(results["page_count"]))
        num_procs = min(len(pages_to_check), max(1, cpu_count() - 1))
        with Pool(processes=num_procs) as pool:
            args = [(pdf_path, idx) for idx in pages_to_check]
            page_results = pool.map(process_page, args)
        for pr in page_results:
            results["color_space_issues"].extend(pr["color_space_issues"])
            results["color_space_images"].extend(pr["color_space_images"])
    
    # Assign slide indices for image preview links
    for i, img in enumerate(results["color_space_images"]):
        img["slide_index"] = i
    # Summarize non-CMYK color-space issues by page for readability
    if results["color_space_issues"]:
        page_counts = {}
        for issue in results["color_space_issues"]:
            m = re.search(r"Image on page (\d+)", issue)
            if m:
                pg = m.group(1)
                page_counts[pg] = page_counts.get(pg, 0) + 1
        grouped = []
        for pg, cnt in sorted(page_counts.items(), key=lambda x: int(x[0])):
            grouped.append(f"{cnt} non-CMYK image{'s' if cnt > 1 else ''} on page {pg}")
        results["color_space_issues"] = grouped
    
    # Check PDF file size (limit 650 MB)
    file_size_bytes = os.path.getsize(pdf_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    results["file_size_mb"] = round(file_size_mb, 2)
    if file_size_bytes > 650 * 1024 * 1024:
        results["file_size_issues"].append(
            f"File size ({file_size_mb:.2f} MB) exceeds KDP limit of 650MB"
        )
    
    doc.close()
    end_time = time.time()
    results["processing_time"] = round(end_time - start_time, 2)
    return results

def check_cover_for_kdp(pdf_path, trim_size, color_option, page_count, book_type='paperback', custom_width=None, custom_height=None):
    # 1) Validate trim size and open PDF
    # Handle custom trim size
    if trim_size == 'custom':
        try:
            trim_w = float(custom_width)
            trim_h = float(custom_height)
        except (TypeError, ValueError):
            return {"error": "Invalid custom trim dimensions for cover validation."}
        if not (4 <= trim_w <= 8.5 and 6 <= trim_h <= 11.69):
            return {"error": "Custom cover trim size out of allowed range."}
    else:
        if trim_size not in KDP_TRIM_SIZES:
            return {"error": f"Trim size '{trim_size}' is not supported for cover validation."}
        trim_w, trim_h, _ = KDP_TRIM_SIZES[trim_size]
    # Bleed/wrap: hardcover uses 0.51" wrap, paperback always 0.125"
    if book_type == 'hardcover':
        bleed = 0.51
    else:
        bleed = 0.125
    doc = fitz.open(pdf_path)
    if len(doc) != 1:
        doc.close()
        return {"error": "Cover PDF must be exactly one page."}
    page = doc[0]

    # 2) Measure cover dimensions (points → inches)
    w_in = page.rect.width / 72.0
    h_in = page.rect.height / 72.0

    # 3) Determine spine thickness by color option
    thickness = {
        "black_white": 0.002252,
        "black_cream":  0.0025,
        "standard_color": 0.002252,
        "premium_color": 0.002347
    }[color_option]
    spine_w = page_count * thickness
    
    # 4) Calculate expected cover dims
    if book_type == 'hardcover':
        # Calibrated to KDP: wrap_bleed = 0.70815" (including bleed+wrap), hinge = 0.346"
        wrap_bleed = 0.70815
        hinge = 0.346
        # width = 2*trim + spine + 2*wrap_bleed + hinge
        exp_w = (2 * trim_w) + spine_w + (2 * wrap_bleed) + hinge
        # height = trim height + 2*wrap_bleed
        exp_h = trim_h + (2 * wrap_bleed)
    else:
        # Paperback: standard bleed around edges
        exp_w = (2 * bleed) + (2 * trim_w) + spine_w
        exp_h = (2 * bleed) + trim_h
    
    # 5) Tolerance check for cover vs expected size
    tol = 0.05
    dim_ok = abs(w_in - exp_w) <= tol and abs(h_in - exp_h) <= tol
    issues = []
    if not dim_ok:
        issues.append(
            f"Cover dimensions ({w_in:.2f}\"×{h_in:.2f}\") don't match expected ({exp_w:.2f}\"×{exp_h:.2f}\")"
        )
    
    # 6) CMYK image scan for cover page
    color_space_issues = []
    color_space_images = []
    if color_option in ["standard_color", "premium_color"]:
        img_results = process_page((pdf_path, 0))
        color_space_issues = img_results.get("color_space_issues", [])
        color_space_images = img_results.get("color_space_images", [])
    
    # 7) Close and return detailed cover results
    doc.close()
    # Breakdown of cover components
    spine_margin = 0.062
    barcode_margin_w, barcode_margin_h = 0.25, 0.375
    if book_type == 'hardcover':
        wrap_val = wrap_bleed
        hinge_val = hinge
    else:
        wrap_val = bleed
        hinge_val = bleed
    breakdown = [
        ("Full Cover", exp_w, exp_h),
        ("Front Cover", trim_w, trim_h),
        ("Margin", bleed, bleed),
        ("Wrap", wrap_val, wrap_val),
        ("Hinge", hinge_val, exp_h),
        ("Spine", spine_w, trim_h),
        ("Spine Safe Area", max(spine_w - 2*spine_margin, 0), max(trim_h - 2*spine_margin, 0)),
        ("Spine Margin", spine_margin, spine_margin),
        ("Barcode Margin", barcode_margin_w, barcode_margin_h)
    ]
    return {
        "cover_dimensions_valid": dim_ok,
        "breakdown": breakdown,
        "actual_width": w_in,
        "actual_height": h_in,
        "expected_width": exp_w,
        "expected_height": exp_h,
        "spine_width": spine_w,
        "bleed_used": bleed,
        "issues": issues,
        "color_space_issues": color_space_issues,
        "color_space_images": color_space_images
    }

def process_page_for_print(args):
    """Process a single page for print issues"""
    pdf_path, page_idx = args
    results = {
        "transparency_issues": [],
        "font_issues": [],
        "color_profile_issues": [],
        "margin_issues": [],
        "resolution_issues": [],
        "preview": None  # Will store preview image
    }
    
    doc = None
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_idx]
        
        # Generate page preview image via PIL to avoid fz_save_pixmap_as_png error
        pix = page.get_pixmap(matrix=fitz.Matrix(0.15, 0.15), alpha=False)
        mode = "RGBA" if pix.alpha else "RGB"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64_preview = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        results["preview"] = {
            "page": page_idx + 1,
            "image": b64_preview,
            "width": pix.width,
            "height": pix.height
        }
        
        # 1. Check for transparency
        # PyMuPDF doesn't directly expose transparency info, indirect approach
        # Save page as PNG with alpha and check for semi-transparent pixels
        pix = page.get_pixmap(alpha=True)
        if pix.alpha:
            # Check for partially transparent pixels (not just fully transparent or opaque)
            alpha_data = pix.samples[3::4]  # Every 4th byte is alpha in RGBA format
            semi_transparent = any(0 < a < 255 for a in alpha_data)
            if semi_transparent:
                results["transparency_issues"].append(f"Page {page_idx+1} contains transparency effects")
        
        # 2. Check embedded fonts
        # Get font info for the page
        font_list = page.get_fonts()
        for font in font_list:
            # font tuple: (xref, name, type, embedded, subset)
            font_name, font_type, is_embedded = font[1], font[2], font[3]
            if not is_embedded:
                results["font_issues"].append(f"Page {page_idx+1} uses non-embedded font: {font_name}")
        
        # 3. Check image resolution and color profile
        image_list = page.get_images(full=True)
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            tmp_path = None
            img_tmp = None
            try:
                img_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                tmp_path = img_tmp.name
                img_tmp.write(image_bytes)
                img_tmp.close()
                
                with Image.open(tmp_path) as img:
                    # Check color mode/profile
                    if img.mode not in ['CMYK', 'L', '1']:  # Not CMYK, grayscale or bitmap
                        results["color_profile_issues"].append(
                            f"Image on page {page_idx+1} (#{img_index+1}) uses {img.mode} color mode instead of CMYK"
                        )
                    
                    # Check image resolution (assuming 72 dpi for PDF)
                    # PyMuPDF gives image size in points, we can estimate resolution
                    width_pt, height_pt = base_image.get("width", 0), base_image.get("height", 0)
                    if width_pt > 0 and height_pt > 0:
                        img_width, img_height = img.size
                        dpi_x = img_width / (width_pt / 72)
                        dpi_y = img_height / (height_pt / 72)
                        if min(dpi_x, dpi_y) < 200:  # Usually 300 DPI is recommended, 200 is minimum
                            results["resolution_issues"].append(
                                f"Image on page {page_idx+1} (#{img_index+1}) has low resolution: ~{int(min(dpi_x, dpi_y))} DPI"
                            )
            finally:
                # Clean up the temp file if it exists
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception as e:
                        print(f"Warning: Could not delete temp file {tmp_path}: {e}")
        
        # 4. Check margins
        # Standard print margins are usually 0.5-0.75 inches (36-54 pts)
        # This is a simple estimate - actual requirements vary by publisher
        MIN_MARGIN = 36  # 0.5 inches in points
        width, height = page.rect.width, page.rect.height
        
        text_areas = page.search_for(".", quads=True)
        if text_areas:
            # Find text boundaries
            left = min(quad.rect.x0 for quad in text_areas)
            right = max(quad.rect.x1 for quad in text_areas)
            top = min(quad.rect.y0 for quad in text_areas)
            bottom = max(quad.rect.y1 for quad in text_areas)
            
            # Check margins
            left_margin, right_margin = left, width - right
            top_margin, bottom_margin = top, height - bottom
            
            if min(left_margin, right_margin, top_margin, bottom_margin) < MIN_MARGIN:
                results["margin_issues"].append(
                    f"Page {page_idx+1} has narrow margins: L:{left_margin/72:.2f}\", R:{right_margin/72:.2f}\", " +
                    f"T:{top_margin/72:.2f}\", B:{bottom_margin/72:.2f}\" (min recommended: 0.5\")"
                )
    except Exception as e:
        print(f"Error processing page {page_idx+1}: {e}")
        for issue_type in results:
            if issue_type != "preview":  # Don't add error message to preview
                results[issue_type].append(f"Error processing page {page_idx+1}: {e}")
    finally:
        # Make sure to close the document
        if doc:
            doc.close()
    
    return results

def check_pdf_for_print_issues(pdf_path, page_range=None, trim_size=None, book_type='paperback', color_option='black_white', include_bleed=False, custom_width=None, custom_height=None):
    """Check PDF for printing issues on specified pages or all pages"""
    start_time = time.time()
    print(f"Starting print issue analysis for {pdf_path}, page range: {page_range}, trim size: {trim_size}, book type: {book_type}, color: {color_option}, include_bleed: {include_bleed}")
    # Compute bleed allowance for margin calculations
    if include_bleed:
        bleed = 0.51 if book_type == 'hardcover' else 0.125
    else:
        bleed = 0.0
    # Validate trim size (custom or predefined)
    if trim_size == 'custom':
        try:
            trim_w = float(custom_width)
            trim_h = float(custom_height)
        except (TypeError, ValueError):
            return {"general_error": "Invalid custom trim dimensions for print issues", "has_issues": True}
        if not (4 <= trim_w <= 8.5 and 6 <= trim_h <= 11.69):
            return {"general_error": "Custom trim size out of allowed range", "has_issues": True}
    else:
        trim_sizes_dict = KDP_TRIM_SIZES if book_type == "paperback" else KDP_HARDCOVER_TRIM_SIZES
        if trim_size not in trim_sizes_dict:
            return {"general_error": f"Selected trim size {trim_size} is not available for {book_type}", "has_issues": True}

    results = {
        "trim_size": trim_size,
        "book_type": book_type,
        "color_option": color_option,
        "include_bleed": include_bleed,
        "custom_width": custom_width,
        "custom_height": custom_height,
        "bleed": bleed,
        "transparency_issues": [],
        "font_issues": [],
        "color_profile_issues": [],
        "margin_issues": [],
        "resolution_issues": [],
        "page_count": 0,
        "processing_time": 0.0,
        "analyzed_pages": [],
        "has_issues": False,
        "page_previews": {}  # Will store preview images by page number
    }
    
    doc = None
    try:
        doc = fitz.open(pdf_path)
        results["page_count"] = len(doc)
        
        # Determine which pages to check
        if page_range:
            try:
                # Parse page range like "1-5,7,9-12"
                pages_to_check = []
                for part in page_range.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        # Convert 1-based page numbers to 0-based indices
                        pages_to_check.extend(range(start-1, end))
                    else:
                        # Convert 1-based page number to 0-based index
                        pages_to_check.append(int(part) - 1)
                # Filter out page numbers that exceed document length
                pages_to_check = [p for p in pages_to_check if 0 <= p < len(doc)]
            except ValueError:
                # If parsing fails, check all pages
                pages_to_check = list(range(len(doc)))
        else:
            # Default to all pages
            pages_to_check = list(range(len(doc)))
        
        # Close the document before multiprocessing to avoid file locking issues
        doc.close()
        doc = None
        
        # Store which pages were analyzed
        results["analyzed_pages"] = [p+1 for p in pages_to_check]  # Convert back to 1-based
        
        # Parallelized processing for image checks
        num_procs = min(len(pages_to_check), max(1, cpu_count() - 1))
        with Pool(processes=num_procs) as pool:
            args = [(pdf_path, idx) for idx in pages_to_check]
            page_results = pool.map(process_page_for_print, args)
            
        # Process results from each page
        for page_result in page_results:
            pr = page_result.get("preview")
            page_num = pr.get("page") if isinstance(pr, dict) else None
            
            # Add page preview if there were any issues on this page
            has_page_issues = any([
                page_result.get("transparency_issues"),
                page_result.get("font_issues"), 
                page_result.get("color_profile_issues"),
                page_result.get("margin_issues"),
                page_result.get("resolution_issues")
            ])
            
            if has_page_issues and page_num and page_result.get("preview"):
                # Enhance preview with issue categories and details
                preview = page_result["preview"]
                categories = []
                issues_by_category = {}
                if page_result.get("transparency_issues"):
                    categories.append("transparency")
                    issues_by_category["transparency"] = page_result["transparency_issues"]
                if page_result.get("font_issues"):
                    categories.append("font")
                    issues_by_category["font"] = page_result["font_issues"]
                if page_result.get("color_profile_issues"):
                    categories.append("color_profile")
                    issues_by_category["color_profile"] = page_result["color_profile_issues"]
                if page_result.get("resolution_issues"):
                    categories.append("resolution")
                    issues_by_category["resolution"] = page_result["resolution_issues"]
                if page_result.get("margin_issues"):
                    categories.append("margin")
                    issues_by_category["margin"] = page_result["margin_issues"]
                preview["categories"] = categories
                preview["issues_by_category"] = issues_by_category
                results["page_previews"][page_num] = preview
            
            if page_result.get("transparency_issues"):
                results["transparency_issues"].extend(page_result["transparency_issues"])
            if page_result.get("font_issues"):
                results["font_issues"].extend(page_result["font_issues"])
            if page_result.get("color_profile_issues"):
                results["color_profile_issues"].extend(page_result["color_profile_issues"])
            if page_result.get("margin_issues"):
                results["margin_issues"].extend(page_result["margin_issues"])
            if page_result.get("resolution_issues"):
                results["resolution_issues"].extend(page_result["resolution_issues"])
        
        # Update the has_issues flag if any issues were found
        results["has_issues"] = any([
            results["transparency_issues"],
            results["font_issues"], 
            results["color_profile_issues"],
            results["margin_issues"],
            results["resolution_issues"]
        ])
        
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        results["general_error"] = str(e)
        results["has_issues"] = True
    finally:
        # Make sure to close the document if it's still open
        if doc:
            doc.close()
    
    end_time = time.time()
    results["processing_time"] = round(end_time - start_time, 2)
    return results

@app.route('/', methods=['GET'])
def index():
    # Pass both trim size options and color options to the template
    return render_template('index.html', 
                          paperback_trim_sizes=list(KDP_TRIM_SIZES.keys()),
                          hardcover_trim_sizes=list(KDP_HARDCOVER_TRIM_SIZES.keys()),
                          color_options=COLOR_OPTIONS)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    temp_file_path = None
    try:
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            temp_file_path = filepath  # Keep track of the file path for cleanup
            
            # Determine validation mode
            validation_mode = request.form.get('validation_mode', 'interior')
            
            # Handle print issues analysis
            if validation_mode == 'print_issues':
                page_range = request.form.get('page_range', '')
                # Get trim size and other parameters
                trim_size = request.form.get('trim_size')
                book_type = request.form.get('book_type', 'paperback')
                color_option = request.form.get('color_option', 'black_white')
                include_bleed = request.form.get('include_bleed', 'false').lower() in ['true', '1', 'yes', 'on']
                custom_width = request.form.get('custom_width')
                custom_height = request.form.get('custom_height')
                results = check_pdf_for_print_issues(
                    filepath,
                    page_range,
                    trim_size=trim_size,
                    book_type=book_type,
                    color_option=color_option,
                    include_bleed=include_bleed,
                    custom_width=custom_width,
                    custom_height=custom_height
                )
                # Render the print issues results template
                response = render_template(
                    'print_issues_results.html',
                    results=results,
                    trim_size=trim_size,
                    color_option=color_option,
                    book_type=book_type,
                    include_bleed=include_bleed
                )
                return response
            
            # Handle cover validation
            if validation_mode == 'cover':
                # Cover needs interior page count to compute spine
                page_count_input = request.form.get('page_count')
                try:
                    page_count = int(page_count_input)
                except (TypeError, ValueError):
                    return jsonify({"error": "Invalid page count for cover validation"}), 400
                
                # Get trim size and other parameters
                trim_size = request.form.get('trim_size')
                book_type = request.form.get('book_type', 'paperback')
                color_option = request.form.get('color_option', 'black_white')
                
                # Pass book_type and any custom dims
                results = check_cover_for_kdp(
                    filepath,
                    trim_size,
                    color_option,
                    page_count,
                    book_type,
                    custom_width=request.form.get('custom_width'),
                    custom_height=request.form.get('custom_height')
                )
                
                # Render cover-specific results
                response = render_template(
                    'cover_results.html',
                    results=results,
                    trim_size=trim_size,
                    color_option=color_option,
                    book_type=book_type,
                    include_bleed=True
                )
                return response
            
            # Handle interior validation (default)
            trim_size = request.form.get('trim_size')
            book_type = request.form.get('book_type', 'paperback')
            color_option = request.form.get('color_option', 'black_white')
            
            # Pass custom dimensions if provided
            custom_width = request.form.get('custom_width')
            custom_height = request.form.get('custom_height')
            results = check_pdf_for_kdp(filepath, trim_size, book_type, color_option, custom_width=custom_width, custom_height=custom_height)
            
            # Determine grouping block size based on total page count
            total_pages = results.get("page_count", 0)
            if total_pages <= 20:
                range_size = total_pages  # single block for small docs
            elif total_pages <= 100:
                range_size = 10
            else:
                range_size = 20
            page_ranges = {}
            # First, group images by page
            pages_images = {}
            for img in results["color_space_images"]:
                pages_images.setdefault(img["page"], []).append(img)
            for page, imgs in pages_images.items():
                start = ((page - 1) // range_size) * range_size + 1
                end = start + range_size - 1
                if end > total_pages:
                    end = total_pages
                range_label = f"Pages {start}-{end}"
                page_ranges.setdefault(range_label, []).extend(imgs)
            
            # Log results before sending
            print(f"Validation results:")
            print(f"  Trim size match: {results['trim_size_match']}")
            print(f"  Page count: {results['page_count']}, valid: {results['page_count_valid']}")
            print(f"  Color space issues: {len(results['color_space_issues'])}")
            print(f"  Color space images: {len(results['color_space_images'])}")
            print(f"  File size: {results['file_size_mb']} MB")
            
            # Render a separate results page with left-right layout
            response = render_template(
                'results.html',
                results=results,
                color_option=color_option,
                color_options=COLOR_OPTIONS,
                include_bleed=False,
                page_ranges=page_ranges
            )
            return response
    finally:
        # Clean up the uploaded file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_file_path}: {e}")
                # Don't raise the exception so the response is still sent

@app.route('/templates/index.html')
def serve_template():
    return render_template('index.html', 
                          paperback_trim_sizes=list(KDP_TRIM_SIZES.keys()),
                          hardcover_trim_sizes=list(KDP_HARDCOVER_TRIM_SIZES.keys()),
                          color_options=COLOR_OPTIONS)

if __name__ == '__main__':
    app.run(debug=True)
