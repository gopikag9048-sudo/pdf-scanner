import os
import tempfile
import subprocess
import uuid
import json
import shutil
from flask import Flask, request, send_file, Response, abort
import fitz  # PyMuPDF
import pikepdf

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO

app = Flask(__name__)

# ----------- Utilities -----------

def run_clamscan(path: str):
    """Return (status, raw_output, exitcode)
       exitcode: 0=clean, 1=infected, 2=error
    """
    proc = subprocess.run(
        ["clamscan", "--no-summary", path],
        capture_output=True, text=True
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    status = "clean" if proc.returncode == 0 else ("infected" if proc.returncode == 1 else "error")
    return status, out.strip(), proc.returncode

def sanitize_pdf(input_path: str, output_path: str):
    """
    Best-effort sanitize using pikepdf:
      - Remove JavaScript (/Names/JavaScript), /OpenAction, /AA
      - Remove /EmbeddedFiles name tree
      - Strip risky annotations: /RichMedia, /FileAttachment, actions with /JavaScript or /Launch
    Keeps text selectable.
    """
    with pikepdf.open(input_path, allow_overwriting_input=True) as pdf:
        # Access document catalog via trailer Root (compatible with newer pikepdf)
        root = pdf.trailer.get("/Root", None)
        if root is not None:
            # Dereference if indirect
            if hasattr(root, "get_object"):
                root = root.get_object()
            if isinstance(root, pikepdf.Dictionary):
                # Remove document-level actions and JS
                for key in ["/OpenAction", "/AA"]:
                    if key in root:
                        del root[key]
                names = root.get("/Names", None)
                if names is not None and hasattr(names, "get_object"):
                    names = names.get_object()
                if isinstance(names, pikepdf.Dictionary):
                    if "/JavaScript" in names:
                        del names["/JavaScript"]
                    if "/EmbeddedFiles" in names:
                        del names["/EmbeddedFiles"]

        # Walk pages to remove risky annotations/actions
        for page in pdf.pages:
            pobj = page.obj  # work with the underlying dictionary
            for key in ["/AA"]:
                if key in pobj:
                    del pobj[key]
            annots = pobj.get("/Annots", None)
            if isinstance(annots, pikepdf.Array):
                new_annots = pikepdf.Array()
                for aref in annots:
                    annot = aref.get_object() if hasattr(aref, "get_object") else aref
                    subtype = annot.get("/Subtype", None)
                    # Strip rich media & file attachments
                    if subtype in [pikepdf.Name("/RichMedia"), pikepdf.Name("/FileAttachment")]:
                        continue
                    a = annot.get("/A", None)
                    if isinstance(a, pikepdf.Dictionary):
                        s = a.get("/S", None)
                        if s in [pikepdf.Name("/JavaScript"), pikepdf.Name("/Launch"), pikepdf.Name("/SubmitForm"), pikepdf.Name("/ImportData")]:
                            # drop this annotation entirely
                            continue
                    # Also drop explicit /JS keys if present
                    if "/JS" in annot:
                        continue
                    new_annots.append(aref)
                if len(new_annots):
                    pobj["/Annots"] = new_annots
                else:
                    if isinstance(pobj, pikepdf.Dictionary):
                        if "/Annots" in pobj:
                         del pobj["/Annots"]

        # Save sanitized PDF
        pdf.save(output_path, linearize=True)

def rasterize_pdf(input_path: str, output_path: str, dpi: int = 200):
    """
    Maximum safety: render each page to an image and rebuild a PDF containing only images.
    Destroys active content; output is safe but not selectable text.
    """
    src = fitz.open(input_path)
    out = fitz.open()
    for page in src:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        # Create a new PDF page with same aspect ratio as raster
        rect = fitz.Rect(0, 0, pix.width, pix.height)
        p = out.new_page(width=rect.width, height=rect.height)
        p.insert_image(rect, stream=pix.tobytes(), keep_proportion=False)
    out.save(output_path, deflate=True, garbage=4)

def build_report(steps):
    """
    Create a human-readable narrative report in plain text.
    Includes detailed descriptions for clean and infected cases.
    """
    report = []
    report.append("PDF Scan and Sanitization Report")
    report.append("=" * 40)
    report.append("")

    # ---- Describe each step ----
    for step in steps:
        stage = step['stage'].replace('_', ' ').title()
        status = step['status']
        code = step['exit_code']

        if step['stage'] == "pre_scan":
            if status == "infected":
                report.append(f"1. The uploaded PDF was first scanned using ClamAV. The initial scan detected infections (exit code {code}).")
                report.append("   This indicates that the original PDF may contain malicious content such as embedded JavaScript or file attachments.")
            elif status == "clean":
                report.append(f"1. The uploaded PDF was first scanned using ClamAV. The initial scan found no infections (exit code {code}), indicating the file appeared safe.")
            else:
                report.append(f"1. The initial scan encountered an error (exit code {code}). The process continued with sanitization as a precaution.")
            report.append("")

        elif step['stage'] == "post_scan":
            if status == "infected":
                report.append(f"2. After sanitization, the PDF was scanned again. Unfortunately, the scan still detected infections (exit code {code}).")
                report.append("   As a safety measure, the system then attempted to fully rasterize the document — converting each page to an image — to ensure all active content was removed.")
            elif status == "clean":
                report.append(f"2. After sanitization, the file was scanned again. The scan reported it as clean (exit code {code}), confirming that the sanitization successfully removed any risky elements.")
            else:
                report.append(f"2. The post-sanitization scan encountered an error (exit code {code}). The process continued with additional safety checks.")
            report.append("")

        elif step['stage'] == "post_scan_fallback_rasterize":
            if status == "infected":
                report.append(f"3. Even after rasterizing the PDF, the scan still detected infections (exit code {code}).")
                report.append("   This means the file might still contain malicious signatures that could not be neutralized automatically.")
            elif status == "clean":
                report.append(f"3. The system performed a fallback rasterization, converting each page into a static image. After this step, the scan confirmed the file is clean (exit code {code}).")
                report.append("   The resulting file is completely safe but no longer contains selectable text (only images).")
            else:
                report.append(f"3. The rasterized file scan resulted in an error (exit code {code}). Further manual inspection may be required.")
            report.append("")


        report.append("🧩 Scan Logs:")
        log_text = step.get("log", "")
        for line in log_text.splitlines():
            if line.strip():
                report.append(f"   {line.strip()}")
        report.append("")


    # ---- Overall summary ----
    final_status = steps[-1]['status'] if steps else "unknown"
    if final_status == "clean":
        report.append("Final Result:")
        report.append("The PDF has been successfully processed and verified as clean. It is considered safe to open and share.")
    elif final_status == "infected":
        report.append("Final Result:")
        report.append("Despite sanitization attempts, the final version of the PDF remains infected. It is NOT safe to open or distribute without manual inspection.")
    else:
        report.append("Final Result:")
        report.append("An error occurred during scanning or sanitization, and the file’s safety could not be fully verified.")

    report.append("")
    report.append("This report was generated automatically by the PDF Sanitization API.")
    return "\n".join(report)

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

def generate_pdf_report(steps, output_path, logo_path="static/logoo.png"):
    """
    Generate a professional, readable PDF report with logo, structured headings,
    and the full narrative from build_report() — including infection logs.
    """
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=70, bottomMargin=50
    )

    # Prepare styles
    styles = getSampleStyleSheet()
    story = []

    style_title = ParagraphStyle(
        'Title', fontName="Helvetica-Bold", fontSize=18, alignment=TA_CENTER, spaceAfter=14
    )
    style_heading = ParagraphStyle(
        'Heading', fontName="Helvetica-Bold", fontSize=13,
        textColor=colors.darkblue, spaceBefore=12, spaceAfter=6
    )
    style_normal = ParagraphStyle(
        'Normal', fontName="Helvetica", fontSize=11, leading=16
    )
    style_log = ParagraphStyle(
        'Log', fontName="Courier", fontSize=9,
        backColor=colors.whitesmoke, leftIndent=10,
        spaceBefore=2, spaceAfter=2, leading=11
    )
    style_footer = ParagraphStyle(
        'Footer', fontName="Helvetica-Oblique", fontSize=9,
        textColor=colors.gray, alignment=TA_CENTER
    )

    # --- HEADER ---
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=100, height=60))
    story.append(Spacer(1, 10))
    story.append(Paragraph("PDF Scan & Sanitization Report", style_title))
    story.append(Paragraph(f"Report ID: {uuid.uuid4().hex[:8].upper()}", style_normal))
    story.append(Spacer(1, 10))

    # --- SUMMARY TABLE (Stage / Status / Exit Code) ---
    table_data = [["Stage", "Status", "Exit Code"]]
    for s in steps:
        table_data.append([s["stage"].replace("_", " ").title(), s["status"].capitalize(), str(s["exit_code"])])
    table = Table(table_data, colWidths=[180, 120, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))

    # --- DETAILED NARRATIVE FROM build_report() ---
    from textwrap import wrap
    report_text = build_report(steps)

    # Break into paragraphs to maintain formatting
    for line in report_text.split("\n"):
        if not line.strip():
            story.append(Spacer(1, 5))
            continue
        if line.strip().startswith("🧩"):
            # Log header
            story.append(Paragraph(line.strip(), style_heading))
        elif line.strip().startswith("   "):
            # Log line
            story.append(Paragraph(line.strip(), style_log))
        elif line.strip().endswith(":"):
            # Section headers like “Final Result:”
            story.append(Spacer(1, 8))
            story.append(Paragraph(f"<b>{line.strip()}</b>", style_heading))
        else:
            # Regular paragraph
            story.append(Paragraph(line.strip(), style_normal))

    # --- FOOTER ---
    story.append(Spacer(1, 25))
    story.append(Paragraph("This report was generated automatically by the PDF Sanitization API.", style_footer))

    # --- BUILD PDF ---
    doc.build(story)

# ----------- API -----------

@app.route("/health", methods=["GET"])
def health():
    return {"ok": True}

@app.route("/scan", methods=["POST"])
def scan():
    if "file" not in request.files:
        return abort(400, "No file provided")

    mode = request.form.get("mode", "sanitize")  # 'sanitize' or 'rasterize'
    return_report = request.form.get("report", "0") == "1"

    f = request.files["file"]
    if not f.filename.lower().endswith(".pdf"):
        return abort(400, "Not a PDF")

    # Work in temp directory
    workdir = tempfile.mkdtemp(prefix="scanpdf_")
    steps = []
    try:
        in_path = os.path.join(workdir, "input.pdf")
        f.save(in_path)

        # 1) Initial scan
        status1, log1, code1 = run_clamscan(in_path)
        steps.append({"stage": "pre_scan", "status": status1, "exit_code": code1, "log": log1})

        cleaned_path = os.path.join(workdir, "cleaned.pdf")

        if mode == "rasterize":
            # Max safety
            rasterize_pdf(in_path, cleaned_path)
        else:
            # Try sanitize first
            sanitize_pdf(in_path, cleaned_path)

        # 2) Post-clean scan
        status2, log2, code2 = run_clamscan(cleaned_path)
        steps.append({"stage": "post_scan", "status": status2, "exit_code": code2, "log": log2})

        # If sanitize failed to neutralize, fall back to rasterize
        if mode == "sanitize" and code2 != 0:
            fallback_path = os.path.join(workdir, "cleaned_raster.pdf")
            rasterize_pdf(in_path, fallback_path)
            status3, log3, code3 = run_clamscan(fallback_path)
            steps.append({"stage": "post_scan_fallback_rasterize", "status": status3, "exit_code": code3, "log": log3})
            cleaned_path = fallback_path

        if return_report:
            # Generate PDF report instead of text
            import zipfile
            pdf_report_path = os.path.join(workdir, "report.pdf")
            generate_pdf_report(steps, pdf_report_path, logo_path="static/logo.png")

            zip_path = os.path.join(workdir, "result.zip")
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.write(cleaned_path, "cleaned.pdf")
                z.write(pdf_report_path, "report.pdf")

            return send_file(zip_path, as_attachment=True, download_name="result.zip", mimetype="application/zip")

        return send_file(cleaned_path, as_attachment=True, download_name="cleaned.pdf", mimetype="application/pdf")

    finally:
        # Cleanup temp files
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass

if __name__ == "__main__":
    # Bind to 0.0.0.0 for container
    app.run(host="0.0.0.0", port=8000)
