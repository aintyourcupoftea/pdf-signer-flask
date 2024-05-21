from flask import Flask, request, send_file, jsonify
from io import BytesIO
import tempfile
from PyPDF2 import PdfFileReader, PdfFileWriter
from PIL import Image
import os

app = Flask(__name__)


def sign_pdf(pdf_file, signature_image):
    if not pdf_file or not signature_image:
        return "Please provide both PDF and signature image files.", 400

    # Read PDF
    pdf_reader = PdfFileReader(pdf_file)

    # Convert signature to PDF (handling transparency)
    signature_stream = BytesIO()
    img = Image.open(signature_image)

    # Check if image has an alpha (transparency) channel
    if img.mode == 'RGBA':
        # Create a white background image
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])  # Paste using alpha as mask
        bg.save(signature_stream, format='PDF', resolution=100.0)
    else:
        img.convert("RGB").save(signature_stream, format='PDF', resolution=100.0)

    signature_stream.seek(0)

    # Create a new PDF writer
    pdf_writer = PdfFileWriter()

    # Add all pages from the original PDF to the new writer
    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
        pdf_writer.addPage(page)

    # Add the signature image (now a PDF) to the first page
    first_page = pdf_writer.getPage(0)
    first_page.mergeScaledTranslatedPage(
        PdfFileReader(signature_stream).getPage(0),
        scale=0.2,
        tx=400, ty=50
    )

    # Create the output PDF in memory
    output_stream = BytesIO()
    pdf_writer.write(output_stream)
    output_stream.seek(0)

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(output_stream.getvalue())
        file_path = tmp_file.name

    return file_path


@app.route("/api/sign_pdf", methods=["POST"])
def api_sign_pdf():
    if "pdf_file" not in request.files or "signature_image" not in request.files:
        return jsonify({"error": "Please provide both PDF and signature image files."}), 400

    pdf_file = request.files["pdf_file"]
    signature_image = request.files["signature_image"]

    output_path = sign_pdf(pdf_file, signature_image)

    return send_file(output_path, as_attachment=True, download_name="signed.pdf")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
