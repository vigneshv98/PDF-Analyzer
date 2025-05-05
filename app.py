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
    trim_size = request.form.get('trim_size')
    book_type = request.form.get('book_type', 'paperback')
    color_option = request.form.get('color_option', 'black_white')
    
    print(f"Upload received: {file.filename}, trim: {trim_size}, type: {book_type}, color: {color_option}")
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Determine validation mode (interior vs cover)
        validation_mode = request.form.get('validation_mode', 'interior')
        if validation_mode == 'cover':
            # Cover needs interior page count to compute spine
            page_count_input = request.form.get('page_count')
            try:
                page_count = int(page_count_input)
            except (TypeError, ValueError):
                os.remove(filepath)
                return jsonify({"error": "Invalid page count for cover validation"}), 400
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
            # cleanup upload
            os.remove(filepath)
            # Render cover-specific results
            return render_template(
                'cover_results.html',
                results=results,
                trim_size=trim_size,
                color_option=color_option,
                book_type=book_type,
                include_bleed=True
            )
        
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
        
        # Clean up the uploaded file
        os.remove(filepath)
        
        # Render a separate results page with left-right layout
        return render_template(
            'results.html',
            results=results,
            color_option=color_option,
            color_options=COLOR_OPTIONS,
            include_bleed=False,
            page_ranges=page_ranges
        )

@app.route('/templates/index.html')
def serve_template():
    return render_template('index.html', 
                          paperback_trim_sizes=list(KDP_TRIM_SIZES.keys()),
                          hardcover_trim_sizes=list(KDP_HARDCOVER_TRIM_SIZES.keys()),
                          color_options=COLOR_OPTIONS)

if __name__ == '__main__':
    app.run(debug=True)
