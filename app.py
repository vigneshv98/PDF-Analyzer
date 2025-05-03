import os
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from PIL import Image
import tempfile

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

def check_color_space(image):
    """Check if an image is in CMYK color space"""
    return image.mode == 'CMYK'

def check_pdf_for_kdp(pdf_path, trim_size, book_type="paperback", color_option="black_white"):
    """Check if PDF meets KDP guidelines"""
    results = {
        "trim_size_match": False,
        "color_space_issues": [],
        "page_count": 0,
        "page_count_valid": False,
        "bleed_issues": [],
        "resolution_issues": []
    }
    
    # Select the appropriate trim size data based on book type
    trim_sizes = KDP_TRIM_SIZES if book_type == "paperback" else KDP_HARDCOVER_TRIM_SIZES
    
    # Check if the trim size is valid for the selected book type
    if trim_size not in trim_sizes:
        results["bleed_issues"].append(f"Selected trim size {trim_size} is not available for {book_type}")
        return results
    
    # Check if the color option is valid for the selected trim size
    if color_option not in COLOR_OPTIONS:
        results["color_space_issues"].append(f"Invalid color option: {color_option}")
        return results
    
    # Check if the color option is available for the selected trim size
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
    
    # Check trim size (accounting for bleed)
    target_width, target_height = trim_data[0], trim_data[1]
    bleed_allowance = 0.125  # Standard 1/8 inch bleed
    
    # Check with bleed allowance
    width_with_bleed = target_width + (2 * bleed_allowance)
    height_with_bleed = target_height + (2 * bleed_allowance)
    
    # Tolerances for comparison (0.05 inch)
    tolerance = 0.05
    
    if (abs(width_in - width_with_bleed) <= tolerance and 
        abs(height_in - height_with_bleed) <= tolerance):
        results["trim_size_match"] = True
    elif (abs(width_in - target_width) <= tolerance and 
          abs(height_in - target_height) <= tolerance):
        results["trim_size_match"] = True
        results["bleed_issues"].append("PDF dimensions match trim size but don't include bleed")
    else:
        results["bleed_issues"].append(f"PDF dimensions ({width_in:.2f}\" x {height_in:.2f}\") don't match selected trim size ({target_width}\" x {target_height}\") with or without bleed")
    
    # Check images on each page (only for color options that require CMYK)
    if color_option in ["standard_color", "premium_color"]:
        for page_num, page in enumerate(doc):
            # Extract images
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Convert to PIL Image
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(image_bytes)
                    temp_file_path = temp_file.name
                
                try:
                    with Image.open(temp_file_path) as img:
                        # Check color space
                        if not check_color_space(img):
                            results["color_space_issues"].append(f"Image on page {page_num+1} (#{img_index+1}) is not in CMYK color space")
                        
                        # Check resolution
                        if img.width < 300 or img.height < 300:
                            results["resolution_issues"].append(f"Image on page {page_num+1} (#{img_index+1}) has low resolution")
                except Exception as e:
                    results["color_space_issues"].append(f"Error processing image on page {page_num+1}: {str(e)}")
                finally:
                    # Clean up
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
    
    doc.close()
    return results

@app.route('/', methods=['GET'])
def index():
    # Pass both trim size options and color options to the template
    return render_template('index.html', 
                          paperback_trim_sizes=KDP_TRIM_SIZES.keys(),
                          hardcover_trim_sizes=KDP_HARDCOVER_TRIM_SIZES.keys(),
                          color_options=COLOR_OPTIONS)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    trim_size = request.form.get('trim_size')
    book_type = request.form.get('book_type', 'paperback')
    color_option = request.form.get('color_option', 'black_white')
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Select the appropriate trim size dictionary based on book type
    trim_sizes = KDP_TRIM_SIZES if book_type == "paperback" else KDP_HARDCOVER_TRIM_SIZES
    
    if not trim_size or trim_size not in trim_sizes:
        return jsonify({"error": "Invalid trim size"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        results = check_pdf_for_kdp(filepath, trim_size, book_type, color_option)
        
        # Clean up the uploaded file
        os.remove(filepath)
        
        return jsonify(results)

@app.route('/templates/index.html')
def serve_template():
    return render_template('index.html', 
                          paperback_trim_sizes=KDP_TRIM_SIZES.keys(),
                          hardcover_trim_sizes=KDP_HARDCOVER_TRIM_SIZES.keys(),
                          color_options=COLOR_OPTIONS)

if __name__ == '__main__':
    app.run(debug=True)
