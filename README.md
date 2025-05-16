# KDP PDF Validator

A web application to validate PDF files against Amazon KDP (Kindle Direct Publishing) print book guidelines.

## Features

- Upload PDF files for validation
- Choose validation type: interior manuscript, full cover (back+spine+front), or detailed print issues analysis
- Display detailed cover components breakdown (full cover, front cover, margin, wrap, hinge, spine, safe areas)
- Choose between paperback and hardcover book types
- Select from comprehensive list of KDP trim sizes
- Enter custom trim sizes within KDP bounds (Width 4"–8.5", Height 6"–11.69")
- Choose color printing options (black/white, color)
- Check PDF dimensions against selected trim size
- Verify if page count is within KDP limits for selected trim size and color option
- Verify image color spaces (ensuring CMYK for color printing)
- Check for proper bleed settings
- Supports uploads up to 650 MB (cover or interior)
- Perform detailed print issue analysis, checking transparency, font embedding, color profiles, image resolution, and margins (optionally for a specified page range with selected trim settings)

## Setup Instructions

1. Clone this repository or download the source code

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
   This will install Flask, Werkzeug, Jinja2, PyMuPDF, and Pillow.

5. Run the application:
   ```
   python app.py
   ```

6. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## How it Works

1. The application validates PDF files against KDP's official requirements for print books:
   - Checks if the PDF dimensions match the selected trim size or custom dimensions
   - Verifies if the PDF includes the required bleed area (typically 0.125" on all sides)
   - Validates that page count is within allowed limits for the selected trim size and color option
   - For cover validation, requires interior page count input to calculate spine thickness and displays a detailed breakdown of cover components
   - For color printing, extracts images from the PDF and confirms they are in CMYK color space
   - Checks image resolution (recommends 300 DPI or higher)
   - Supports custom trim size input within allowed bounds, applying the same tolerance and page-count limits
   - For print issues analysis, performs deep inspection of transparency effects, font embedding, color profiles, image resolution, and page margins (with page previews).

2. Results are displayed with clear pass/fail indicators for each requirement

## Validation Criteria

- **Trim Size**: PDF dimensions must match the selected KDP trim size (with or without bleed) or a custom size within 4"–8.5" × 6"–11.69".
- **Page Count**: Number of pages must be within KDP's allowed range for the selected trim size and color option
- **Bleed Area**: PDF should include the 0.125" bleed area on all sides
- **Color Space**: For color printing options, all images should be in CMYK color space
- **Image Resolution**: All images should have a resolution of at least 300 DPI
- **Font Embedding**: All fonts must be embedded to ensure proper printing.
- **Transparency**: No semi-transparent elements should remain to avoid printing artifacts.
- **Margins**: Content must be within safe margins (≥0.5 inches on all sides).

## System Requirements

- Python 3.7 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Troubleshooting

- If you encounter an error about missing folders, make sure the `templates` directory is in the same directory as the `app.py` file.
- For issues with PDF processing, ensure your PDF is not corrupted and is properly formatted.
- If the CMYK color space check is failing, convert your images to CMYK using image editing software like Adobe Photoshop before embedding them in your PDF.
- Certain color options may not be available for all trim sizes. The tool will validate this and inform you if there's a conflict. 