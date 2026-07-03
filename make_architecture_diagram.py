"""
One-shot script: produce a one-page PDF diagram of the project architecture.
Run: python make_architecture_diagram.py
Output: output/architecture_diagram.pdf
"""
import math
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = landscape(A4)

NAVY  = colors.HexColor('#1B2A4A')
GREEN = colors.HexColor('#27AE60')
BLUE  = colors.HexColor('#2980B9')
GOLD  = colors.HexColor('#F39C12')
GRAY  = colors.HexColor('#7F8C8D')
DARK  = colors.HexColor('#2C3E50')
WHITE = colors.white


def draw_box(c, x, y, w, h, fill, label, sublabel=None, text_color=WHITE):
    c.setFillColor(fill)
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)

    c.setFillColor(text_color)
    c.setFont('Helvetica-Bold', 10)
    title_y = y + h / 2 + (3 if sublabel else -3)
    c.drawCentredString(x + w / 2, title_y, label)
    if sublabel:
        c.setFont('Helvetica', 7.5)
        c.drawCentredString(x + w / 2, y + h / 2 - 9, sublabel)


def draw_arrow(c, x1, y1, x2, y2, color=GRAY, head=5, width=1.0):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    angle = math.atan2(y2 - y1, x2 - x1)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - head * math.cos(angle - math.pi / 6),
             y2 - head * math.sin(angle - math.pi / 6))
    p.lineTo(x2 - head * math.cos(angle + math.pi / 6),
             y2 - head * math.sin(angle + math.pi / 6))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def draw_layer_label(c, y, text):
    c.setFillColor(GRAY)
    c.setFont('Helvetica-Oblique', 8)
    c.drawString(25, y, text)


def main():
    os.makedirs('output', exist_ok=True)
    out_path = os.path.join('output', 'architecture_diagram.pdf')
    c = canvas.Canvas(out_path, pagesize=landscape(A4))

    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 17)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 38,
                        'Automated Football Match Analysis  -  Architecture')
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 54,
                        'End-to-end pipeline: from raw broadcast footage to annotated video and tactical PDF report')

    box_h = 40
    layer_gap = 38
    top = PAGE_H - 95
    layer_y = [top - i * (box_h + layer_gap) for i in range(5)]

    draw_layer_label(c, layer_y[0] + box_h + 5, 'INPUT')
    draw_layer_label(c, layer_y[1] + box_h + 5, 'PERCEPTION')
    draw_layer_label(c, layer_y[2] + box_h + 5, 'SEMANTICS')
    draw_layer_label(c, layer_y[3] + box_h + 5, 'ANALYTICS')
    draw_layer_label(c, layer_y[4] + box_h + 5, 'OUTPUT')

    # Layer 1: Input
    in_w = 220
    in_x = (PAGE_W - in_w) / 2
    draw_box(c, in_x, layer_y[0], in_w, box_h, GOLD,
             'INPUT VIDEO', '1080p MP4 broadcast clip')

    # Layer 2: Perception (3 boxes)
    perc = [
        ('YOLOv11 + ByteTrack', 'Players, ball, refs / persistent IDs'),
        ('Camera Movement', 'Lucas-Kanade optical flow'),
        ('View Transformer', 'Homography -> field coords (m)'),
    ]
    p_w, p_gap = 230, 12
    p_total = len(perc) * p_w + (len(perc) - 1) * p_gap
    p_start = (PAGE_W - p_total) / 2
    perc_centers = []
    for i, (lbl, sub) in enumerate(perc):
        x = p_start + i * (p_w + p_gap)
        draw_box(c, x, layer_y[1], p_w, box_h, NAVY, lbl, sub)
        perc_centers.append(x + p_w / 2)

    # Layer 3: Semantics (2 boxes)
    sem = [
        ('Team Assigner', 'K-means on jersey colors'),
        ('Player-Ball Assigner', 'Confidence-gated proximity'),
    ]
    s_w, s_gap = 320, 24
    s_total = len(sem) * s_w + (len(sem) - 1) * s_gap
    s_start = (PAGE_W - s_total) / 2
    sem_centers = []
    for i, (lbl, sub) in enumerate(sem):
        x = s_start + i * (s_w + s_gap)
        draw_box(c, x, layer_y[2], s_w, box_h, BLUE, lbl, sub)
        sem_centers.append(x + s_w / 2)

    # Layer 4: Analytics (5 boxes)
    an = [
        ('Pass Detector', 'team / player passes'),
        ('Shot Detector', 'on-off / goals'),
        ('Formation Detector', 'live shape estimate'),
        ('Set Piece Detector', 'corners / FK / pen'),
        ('Speed & Distance', 'm / km/h / sprints'),
    ]
    a_w, a_gap = 142, 8
    a_total = len(an) * a_w + (len(an) - 1) * a_gap
    a_start = (PAGE_W - a_total) / 2
    an_centers = []
    for i, (lbl, sub) in enumerate(an):
        x = a_start + i * (a_w + a_gap)
        draw_box(c, x, layer_y[3], a_w, box_h, GREEN, lbl, sub)
        an_centers.append(x + a_w / 2)

    # Layer 5: Output (3 boxes)
    out = [
        ('Annotated Video', 'Confidence-gated overlays'),
        ('PDF Report', 'Cards / tables / per-player'),
        ('LLM Tactical Analyst', 'Narrative summary'),
    ]
    o_w, o_gap = 230, 14
    o_total = len(out) * o_w + (len(out) - 1) * o_gap
    o_start = (PAGE_W - o_total) / 2
    out_centers = []
    for i, (lbl, sub) in enumerate(out):
        x = o_start + i * (o_w + o_gap)
        draw_box(c, x, layer_y[4], o_w, box_h, DARK, lbl, sub)
        out_centers.append(x + o_w / 2)

    # Connector arrows (one per source-target pair, kept thin & gray)
    def connect(src_centers, src_y, dst_centers, dst_y):
        for sx in src_centers:
            for dx in dst_centers:
                draw_arrow(c, sx, src_y, dx, dst_y, color=colors.HexColor('#BDC3C7'),
                           head=4, width=0.6)

    connect([in_x + in_w / 2], layer_y[0], perc_centers, layer_y[1] + box_h)
    connect(perc_centers, layer_y[1], sem_centers, layer_y[2] + box_h)
    connect(sem_centers, layer_y[2], an_centers, layer_y[3] + box_h)
    connect(an_centers, layer_y[3], out_centers, layer_y[4] + box_h)

    # Footer: tech stack
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 8)
    c.drawCentredString(PAGE_W / 2, 28,
                        'Stack: Python  -  Ultralytics YOLOv11  -  Supervision (ByteTrack)  -  '
                        'OpenCV  -  scikit-learn  -  NumPy / pandas  -  ReportLab  -  Anthropic API')

    c.save()
    print(f'[architecture_diagram] saved -> {out_path}')


if __name__ == '__main__':
    main()
