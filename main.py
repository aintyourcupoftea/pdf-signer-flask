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

    pdf_reader = PdfFileReader(pdf_file)
    signature_stream = BytesIO()
    img = Image.open(signature_image)

    # **Key Change:** Save with transparency directly
    img.save(signature_stream, format='PDF', resolution=100.0, transparency=0)
    signature_stream.seek(0)

    pdf_writer = PdfFileWriter()

    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
        pdf_writer.addPage(page)

    first_page = pdf_writer.getPage(0)
    first_page.mergeScaledTranslatedPage(
        PdfFileReader(signature_stream).getPage(0),
        scale=0.5,
        tx=320, ty=70
    )

    output_stream = BytesIO()
    pdf_writer.write(output_stream)
    output_stream.seek(0)

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
