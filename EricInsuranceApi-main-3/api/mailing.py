import fitz
import io
from flask import Blueprint, request, send_file, jsonify


pdf_replace_bp = Blueprint("pdf_replace", __name__)

@pdf_replace_bp.route('/replace_tokens', methods=['POST'])
def replace_tokens():
    uploaded_file = request.files.get('pdf')
    replacements = request.form.to_dict()

    if not uploaded_file:
        return jsonify({'error': 'No PDF uploaded'}), 400

    try:
        pdf_bytes = uploaded_file.read() #load
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        for page in doc:
            for token, value in replacements.items():
                search_term = f"<<{token}>>"
                matches = page.search_for(search_term)
                for rect in matches:
                    page.draw_rect(rect, fill=(1, 1, 1), color=(1, 1, 1))
                    page.insert_text(rect.tl, value, fontsize=11, color=(0, 0, 0)) #replace

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="filled_letter.pdf"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500