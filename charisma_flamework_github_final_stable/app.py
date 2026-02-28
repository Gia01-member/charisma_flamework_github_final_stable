from flask import Flask, render_template, request, send_file
from io import BytesIO
from datetime import datetime
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from data.content import QUESTIONS, TYPE_RULES, TYPE_COPY, ROADMAP

app = Flask(__name__)

AXES = ["A", "B", "C", "D"]
MAX_PER_AXIS = 16

# ======================================================
# PDFフォント（安定性最優先・1フォント固定）
# ※ fontsフォルダに
#    NotoSansJP-VariableFont_wght.ttf
#    を必ず入れてください
# ======================================================
FONT_PATH = os.path.join(
    os.path.dirname(__file__),
    "fonts",
    "NotoSansJP-VariableFont_wght.ttf"
)

PDF_FONT = "NotoSansJP"
pdfmetrics.registerFont(TTFont(PDF_FONT, FONT_PATH))
# ======================================================

def compute_scores(form):
    scores = {a: 0 for a in AXES}
    for qid, axis, _, reverse in QUESTIONS:
        raw = int(form.get(qid, 0))
        val = 4 - raw if reverse else raw
        scores[axis] += val
    return scores

def pick_type(scores):
    for name, cond in TYPE_RULES:
        if cond(scores):
            return name
    return "バランス型"

def build_pdf(ctype, scores, comment):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont(PDF_FONT, 16)
    c.drawString(20*mm, h - 20*mm, "カリスマ性診断レポート（FlameWork）")

    c.setFont(PDF_FONT, 11)
    c.drawString(20*mm, h - 35*mm, f"タイプ：{ctype}")
    c.drawString(20*mm, h - 45*mm, f"作成日時：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

    c.drawString(20*mm, h - 60*mm, f"A: {scores['A']} / {MAX_PER_AXIS}")
    c.drawString(20*mm, h - 70*mm, f"B: {scores['B']} / {MAX_PER_AXIS}")
    c.drawString(20*mm, h - 80*mm, f"C: {scores['C']} / {MAX_PER_AXIS}")
    c.drawString(20*mm, h - 90*mm, f"D: {scores['D']} / {MAX_PER_AXIS}")

    c.drawString(20*mm, h - 105*mm, comment)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", questions=QUESTIONS)

@app.route("/result", methods=["POST"])
def result():
    scores = compute_scores(request.form)
    ctype = pick_type(scores)
    comment = TYPE_COPY.get(ctype, TYPE_COPY["バランス型"])
    return render_template("result.html", ctype=ctype, scores=scores, comment=comment)

@app.route("/pdf", methods=["POST"])
def pdf():
    ctype = request.form.get("ctype", "バランス型")
    comment = request.form.get("comment", "")
    scores = {
        "A": int(request.form.get("A", 0)),
        "B": int(request.form.get("B", 0)),
        "C": int(request.form.get("C", 0)),
        "D": int(request.form.get("D", 0)),
    }
    buf = build_pdf(ctype, scores, comment)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="flamework_report.pdf")

if __name__ == "__main__":
    app.run(debug=True)
