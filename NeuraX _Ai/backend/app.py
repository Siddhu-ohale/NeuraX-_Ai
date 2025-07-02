from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
from tatchi import execute_command
import json
import time
from functools import wraps
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate
from werkzeug.utils import secure_filename
import io
import traceback

app = Flask(__name__, 
    static_folder=os.path.abspath('../frontend'),
    template_folder=os.path.abspath('../frontend'))

# Configure CORS properly for local development
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

request_history = {}
RATE_LIMIT = 10
TIME_WINDOW = 60

# PDF conversion configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        current_time = time.time()
        
        request_history[ip] = [t for t in request_history.get(ip, []) 
                             if current_time - t < TIME_WINDOW]
        
        if len(request_history.get(ip, [])) >= RATE_LIMIT:
            return jsonify({
                "error": "Too many requests. Please wait a moment before trying again."
            }), 429
            
        request_history.setdefault(ip, []).append(current_time)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/convert-to-pdf', methods=['POST'])
@rate_limit
def convert_to_pdf():
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images uploaded'}), 400

        images = request.files.getlist('images')
        if not images or len(images) == 0:
            return jsonify({'error': 'No images selected'}), 400

        pdf_name = request.form.get('pdf_name', 'output')
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=(612, 792))  # Letter size

        for image in images:
            if image and image.filename:
                temp_path = None
                try:
                    filename = secure_filename(image.filename)
                    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(temp_path)

                    with Image.open(temp_path) as img:
                        if img.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'RGBA':
                                background.paste(img, mask=img.split()[3])
                            else:
                                background.paste(img, mask=img.split()[1])
                            img = background
                        
                        # Calculate dimensions
                        img_width, img_height = img.size
                        available_width = 550
                        available_height = 730
                        
                        scale_factor = min(available_width/float(img_width), 
                                        available_height/float(img_height))
                        new_width = int(img_width * scale_factor)
                        new_height = int(img_height * scale_factor)
                        
                        x_centered = (612 - new_width) / 2
                        y_centered = (792 - new_height) / 2

                        c.setFillColorRGB(1, 1, 1)
                        c.rect(0, 0, 612, 792, fill=1)
                        
                        c.drawInlineImage(img, x_centered, y_centered, 
                                       width=new_width, height=new_height)
                        c.showPage()

                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

        c.save()
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{pdf_name}.pdf"
        )

    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/convert-text-to-pdf', methods=['POST'])
@rate_limit
def convert_text_to_pdf():
    try:
        if 'text_content' not in request.form:
            return jsonify({'error': 'No text content provided'}), 400

        text_content = request.form['text_content']
        pdf_name = request.form.get('pdf_name', 'output')
        font_size = int(request.form.get('font_size', '14'))
        is_bold = request.form.get('is_bold', 'false').lower() == 'true'
        is_italic = request.form.get('is_italic', 'false').lower() == 'true'
        is_underline = request.form.get('is_underline', 'false').lower() == 'true'

        # Create PDF buffer
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Create styles
        styles = getSampleStyleSheet()
        custom_style = ParagraphStyle(
            'CustomStyle',
            parent=styles['Normal'],
            fontSize=font_size,
            leading=font_size * 1.2,
        )
        
        if is_bold:
            custom_style.fontName = 'Helvetica-Bold'
        if is_italic:
            custom_style.fontName = 'Helvetica-Oblique'
        if is_bold and is_italic:
            custom_style.fontName = 'Helvetica-BoldOblique'
        
        # Create paragraph with text content
        paragraph = Paragraph(text_content.replace('\n', '<br/>'), custom_style)
        
        # Build PDF
        doc.build([paragraph])
        
        # Get PDF content and return
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{pdf_name}.pdf"
        )

    except Exception as e:
        print(f"Error during text conversion: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('../frontend/css', path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('../frontend/js', path)

@app.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('../frontend/images', path)

@app.route('/Tatchi ai icon.jpg')
def serve_icon():
    return send_from_directory(app.static_folder, 'Tatchi ai icon.jpg')

@app.route('/message', methods=['POST'])
@rate_limit
def message():
    try:
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON format",
                "details": "Please send your message in JSON format with a 'message' field"
            }), 400
            
        data = request.get_json()
        if not isinstance(data, dict) or 'message' not in data:
            return jsonify({
                "error": "Invalid request format",
                "details": "Request must include a 'message' field"
            }), 400
            
        user_msg = data['message']
        if not isinstance(user_msg, str):
            return jsonify({
                "error": "Message must be a string",
                "details": "The 'message' field must contain text"
            }), 400
            
        if not user_msg.strip():
            return jsonify({
                "error": "Empty message",
                "details": "Please provide a non-empty message"
            }), 400

        response = execute_command(user_msg.strip())
        return jsonify(response)
        
    except json.JSONDecodeError:
        return jsonify({
            "error": "Invalid JSON",
            "details": "The request body contains invalid JSON"
        }), 400
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5000, debug=True)