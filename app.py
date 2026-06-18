import io, json
from flask import Flask, render_template, request, send_file, jsonify
from PyPDF2 import PdfReader
from pdf_engine import (
    validate_pdf, merge, split, reorder, extract,
    crop_pages, add_page_numbers, add_watermark,
    read_metadata, edit_metadata, encrypt, decrypt_remove,
    parse_ranges, compress_pdf, images_to_pdf,
    redact_pdf, add_image_watermark, normalize_pages, add_bookmarks,
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB


# ── Error handlers ──

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 100 MB.'}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ── Index ──

@app.route('/')
def index():
    return render_template('index.html')


# ── Process (editor: reorder, rotate, delete, insert) ──

@app.route('/process', methods=['POST'])
def process():
    data = request.form.get('data')
    if not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        ops = json.loads(data)
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data'}), 400

    order = ops.get('order', [])
    if not order:
        return jsonify({'error': 'No pages to process'}), 400

    rotations = ops.get('rotations', {})
    num_files = ops.get('numFiles', 1)
    mode = ops.get('mode', 'standard')

    files = []
    for i in range(num_files):
        f = request.files.get(f'pdf_{i}')
        if not f:
            return jsonify({'error': f'Missing file for source {i}'}), 400
        files.append(f)

    try:
        pdf_bytes = reorder(files, order, rotations, mode)
    except Exception as e:
        return jsonify({'error': f'Processing failed: {e}'}), 400

    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='edited.pdf')


# ── Merge ──

@app.route('/merge', methods=['POST'])
def merge_route():
    files = request.files.getlist('pdfs')
    valid = [f for f in files if f and f.filename]
    if len(valid) < 2:
        return jsonify({'error': 'Upload at least two PDF files'}), 400
    try:
        pdf_bytes = merge(valid)
    except Exception as e:
        return jsonify({'error': f'Merge failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='merged.pdf')


# ── Split ──

@app.route('/split', methods=['POST'])
def split_route():
    file = request.files.get('pdf')
    if not file or not file.filename:
        return jsonify({'error': 'No file uploaded'}), 400

    ranges = request.form.get('ranges', '').strip()
    try:
        valid, err = validate_pdf(file)
        if not valid:
            return jsonify({'error': f'Invalid PDF: {err}'}), 400
        file.seek(0)
        reader = PdfReader(file)
        total = len(reader.pages)
        pages = parse_ranges(ranges, total) if ranges else list(range(1, total + 1))
        file.seek(0)
        zip_bytes = split(file, pages)
    except Exception as e:
        return jsonify({'error': f'Split failed: {e}'}), 400

    return send_file(io.BytesIO(zip_bytes), mimetype='application/zip',
                     as_attachment=True, download_name='split_pages.zip')


# ── Extract pages ──

@app.route('/extract', methods=['POST'])
def extract_route():
    file = request.files.get('pdf')
    data = request.form.get('data')
    if not file or not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        indices = json.loads(data)
        if not indices:
            return jsonify({'error': 'No pages selected'}), 400
        pdf_bytes = extract(file, indices)
    except Exception as e:
        return jsonify({'error': f'Extract failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='extracted.pdf')


# ── Crop ──

@app.route('/crop', methods=['POST'])
def crop_route():
    file = request.files.get('pdf')
    data = request.form.get('data')
    if not file or not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        params = json.loads(data)
        pdf_bytes = crop_pages(
            file,
            page_indices=params.get('pages'),
            left=params.get('left', 0),
            bottom=params.get('bottom', 0),
            right=params.get('right', 612),
            top=params.get('top', 792),
        )
    except Exception as e:
        return jsonify({'error': f'Crop failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='cropped.pdf')


# ── Page numbers ──

@app.route('/pagenumbers', methods=['POST'])
def pagenumbers_route():
    file = request.files.get('pdf')
    data = request.form.get('data')
    if not file or not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        p = json.loads(data)
        pdf_bytes = add_page_numbers(
            file,
            fmt=p.get('format', '{n}'),
            start=p.get('start', 1),
            x=p.get('x', -1),
            y=p.get('y', 30),
            font_size=p.get('fontSize', 10),
            color=tuple(p.get('color', [0, 0, 0])),
        )
    except Exception as e:
        return jsonify({'error': f'Failed to add page numbers: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='numbered.pdf')


# ── Watermark (text) ──

@app.route('/watermark', methods=['POST'])
def watermark_route():
    file = request.files.get('pdf')
    data = request.form.get('data')
    if not file or not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        p = json.loads(data)
        pdf_bytes = add_watermark(
            file,
            text=p.get('text', 'DRAFT'),
            opacity=p.get('opacity', 0.3),
            font_size=p.get('fontSize', 48),
            color=tuple(p.get('color', [0.5, 0.5, 0.5])),
        )
    except Exception as e:
        return jsonify({'error': f'Watermark failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='watermarked.pdf')


# ── Image watermark ──

@app.route('/watermark-image', methods=['POST'])
def watermark_image_route():
    file = request.files.get('pdf')
    image_file = request.files.get('image')
    if not file or not image_file:
        return jsonify({'error': 'Missing PDF or image file'}), 400
    try:
        opacity = float(request.form.get('opacity', 0.3))
        scale = float(request.form.get('scale', 0.5))
        pdf_bytes = add_image_watermark(file, image_file, opacity, scale)
    except Exception as e:
        return jsonify({'error': f'Image watermark failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='watermarked.pdf')


# ── Compress ──

@app.route('/compress', methods=['POST'])
def compress_route():
    file = request.files.get('pdf')
    if not file or not file.filename:
        return jsonify({'error': 'No file uploaded'}), 400
    try:
        valid, err = validate_pdf(file)
        if not valid:
            return jsonify({'error': f'Invalid PDF: {err}'}), 400
        file.seek(0)
        pdf_bytes = compress_pdf(file)
    except Exception as e:
        return jsonify({'error': f'Compression failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='compressed.pdf')


# ── JPG to PDF ──

@app.route('/jpg-to-pdf', methods=['POST'])
def jpg_to_pdf_route():
    files = request.files.getlist('images')
    valid = [f for f in files if f and f.filename]
    if not valid:
        return jsonify({'error': 'Upload at least one image'}), 400
    try:
        orientation = request.form.get('orientation', 'auto')
        pdf_bytes = images_to_pdf(valid, orientation)
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='converted.pdf')


# ── Redact ──

@app.route('/redact', methods=['POST'])
def redact_route():
    file = request.files.get('pdf')
    data = request.form.get('data')
    if not file or not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        payload = json.loads(data)
        if payload.get('__all__'):
            rect = payload['rect']
            file.seek(0)
            reader = PdfReader(file)
            file.seek(0)
            regions = {i: [tuple(rect)] for i in range(len(reader.pages))}
        else:
            if not isinstance(payload, dict):
                return jsonify({'error': 'Invalid regions format'}), 400
            regions = payload
        pdf_bytes = redact_pdf(file, regions)
    except Exception as e:
        return jsonify({'error': f'Redaction failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='redacted.pdf')


# ── Normalize page size ──

@app.route('/normalize', methods=['POST'])
def normalize_route():
    file = request.files.get('pdf')
    if not file or not file.filename:
        return jsonify({'error': 'No file uploaded'}), 400
    try:
        tw = float(request.form.get('target_width', 612))
        th = float(request.form.get('target_height', 792))
        pdf_bytes = normalize_pages(file, tw, th)
    except Exception as e:
        return jsonify({'error': f'Normalize failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='normalized.pdf')


# ── Add bookmarks ──

@app.route('/bookmarks', methods=['POST'])
def bookmarks_route():
    file = request.files.get('pdf')
    data = request.form.get('data')
    if not file or not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        bm_list = json.loads(data)
        if not isinstance(bm_list, list):
            return jsonify({'error': 'Bookmarks must be a list'}), 400
        pdf_bytes = add_bookmarks(file, bm_list)
    except Exception as e:
        return jsonify({'error': f'Bookmarks failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='bookmarked.pdf')


# ── Read metadata ──

@app.route('/metadata', methods=['POST'])
def metadata_read():
    file = request.files.get('pdf')
    if not file:
        return jsonify({'error': 'No file'}), 400
    try:
        meta = read_metadata(file)
    except Exception as e:
        return jsonify({'error': f'Failed to read metadata: {e}'}), 400
    return jsonify(meta)


# ── Edit metadata ──

@app.route('/metadata/edit', methods=['POST'])
def metadata_edit():
    file = request.files.get('pdf')
    data = request.form.get('data')
    if not file or not data:
        return jsonify({'error': 'Missing data'}), 400
    try:
        p = json.loads(data)
        pdf_bytes = edit_metadata(file, **p)
    except Exception as e:
        return jsonify({'error': f'Failed to edit metadata: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='metadata.pdf')


# ── Encrypt ──

@app.route('/encrypt', methods=['POST'])
def encrypt_route():
    file = request.files.get('pdf')
    password = request.form.get('password', '')
    if not file:
        return jsonify({'error': 'No file'}), 400
    if not password:
        return jsonify({'error': 'Password required'}), 400
    try:
        pdf_bytes = encrypt(file, password)
    except Exception as e:
        return jsonify({'error': f'Encryption failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='encrypted.pdf')


# ── Decrypt ──

@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    file = request.files.get('pdf')
    password = request.form.get('password', '')
    if not file:
        return jsonify({'error': 'No file'}), 400
    try:
        pdf_bytes = decrypt_remove(file, password)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {e}'}), 400
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name='decrypted.pdf')


# ── Validate ──

@app.route('/validate', methods=['POST'])
def validate_route():
    file = request.files.get('pdf')
    if not file:
        return jsonify({'valid': False, 'error': 'No file'})
    valid, error = validate_pdf(file)
    return jsonify({'valid': valid, 'error': error})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
