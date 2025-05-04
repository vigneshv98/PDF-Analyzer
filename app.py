import os
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from PIL import Image
import tempfile
import base64
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

def check_pdf_for_kdp(pdf_path, trim_size, book_type="paperback", color_option="black_white", include_bleed=False, custom_width=None, custom_height=None):
    """Check if PDF meets KDP guidelines"""
    print(f"Starting PDF check for {pdf_path}, trim size: {trim_size}, book type: {book_type}, color: {color_option}, include_bleed: {include_bleed}")
    results = {
        "trim_size_match": False,
        "color_space_issues": [],
        "color_space_images": [],
        "page_count": 0,
        "page_count_valid": False,
        "bleed_issues": [],
        "file_size_mb": 0.0,
        "file_size_issues": []
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
    
    # Check images on each page (only for color options that require CMYK)
    if color_option in ["standard_color", "premium_color"]:
        print(f"Color option requires CMYK check: {color_option}")
        for page_num, page in enumerate(doc):
            # Extract images
            image_list = page.get_images(full=True)
            print(f"Page {page_num+1}: Found {len(image_list)} images")
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                print(f"  Processing image #{img_index+1}, xref: {xref}")
                
                # Convert to PIL Image
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(image_bytes)
                    temp_file_path = temp_file.name
                
                try:
                    with Image.open(temp_file_path) as img:
                        print(f"  Image mode: {img.mode}, size: {img.width}x{img.height}")
                        # Check color space
                        if not check_color_space(img):
                            issue_msg = f"Image on page {page_num+1} (#{img_index+1}) is not in CMYK color space"
                            results["color_space_issues"].append(issue_msg)
                            print(f"  NOT CMYK: {issue_msg}")
                            
                            # Create a thumbnail for UI display
                            thumbnail_size = (150, 150)
                            img_copy = img.copy()
                            img_copy.thumbnail(thumbnail_size, Image.LANCZOS)
                            
                            # Convert to Base64 for sending to frontend
                            buffer = io.BytesIO()
                            img_copy.save(buffer, format="PNG")
                            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                            img_size = len(img_base64)
                            print(f"  Created thumbnail, base64 size: {img_size} bytes")
                            
                            # Add the image and metadata to results
                            results["color_space_images"].append({
                                "image": img_base64,
                                "page": page_num+1,
                                "index": img_index+1,
                                "width": img.width,
                                "height": img.height,
                                "mode": img.mode
                            })
                except Exception as e:
                    results["color_space_issues"].append(f"Error processing image on page {page_num+1}: {str(e)}")
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
    
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
    trim_size = request.form.get('trim_size')
    book_type = request.form.get('book_type', 'paperback')
    color_option = request.form.get('color_option', 'black_white')
    include_bleed = request.form.get('include_bleed', 'false') == 'true'
    
    print(f"Upload received: {file.filename}, trim: {trim_size}, type: {book_type}, color: {color_option}, include_bleed: {include_bleed}")
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Pass custom dimensions if provided
        custom_width = request.form.get('custom_width')
        custom_height = request.form.get('custom_height')
        results = check_pdf_for_kdp(filepath, trim_size, book_type, color_option, include_bleed, custom_width, custom_height)
        
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
            include_bleed=include_bleed,
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
