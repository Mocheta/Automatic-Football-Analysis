"""Dark-themed infographic match report (single-page poster style).

Public entry point ``save_pdf(pdf_path, match_name, structured_data, analysis_text)``
is unchanged so ``llm_analyst.generate_report`` keeps working.

Design language (mirrors match_report.png):
  - near-black background, teal = Team 1 / HOME, gold = Team 2 / AWAY
  - score header, numbered section headers (01..05)
  - diverging (mirrored) horizontal bar charts for the shots & passing block
  - set-piece stat cells, two player-performance panels with mini bars
  - AI analysis with a match overview and two "Tips" boxes
"""
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
)
from reportlab.lib.enums import TA_LEFT
from datetime import datetime

# ── Page geometry ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = 768, 1680
L_MARGIN = R_MARGIN = 40
TOP_MARGIN = 78
BOTTOM_MARGIN = 50
W = PAGE_W - L_MARGIN - R_MARGIN          # content width

# ── Colour palette ────────────────────────────────────────────────────────────
BG      = colors.HexColor('#0A0E14')      # page background
PANEL   = colors.HexColor('#121A24')      # card / box background
TRACK   = colors.HexColor('#1E2733')      # empty bar track
LINE    = colors.HexColor('#243040')      # hairline divider
TEAL    = colors.HexColor('#2DD4BF')      # Team 1 / HOME
GOLD    = colors.HexColor('#F4A82E')      # Team 2 / AWAY
WHITE   = colors.HexColor('#F2F5F7')
GRAY    = colors.HexColor('#7C8A99')      # secondary / muted text
DGRAY   = colors.HexColor('#4C5A6A')


# ── Paragraph helpers ─────────────────────────────────────────────────────────

def _p(text, size=9, font='Helvetica', color=WHITE, align=TA_LEFT,
       leading=None, space_before=0, space_after=0, left_indent=0):
    return Paragraph(text, ParagraphStyle(
        '_', fontSize=size, fontName=font, textColor=color, alignment=align,
        leading=leading or size + 4, spaceBefore=space_before,
        spaceAfter=space_after, leftIndent=left_indent))


# ── Section header (01  TITLE  ─────────────) ─────────────────────────────────

class SectionHeader(Flowable):
    def __init__(self, number, title, width=W, accent=TEAL):
        super().__init__()
        self.number, self.title, self.width, self.accent = number, title, width, accent
        self.height = 30

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.accent)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(0, self.height - 13, self.number)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(26, self.height - 15, self.title.upper())
        c.setStrokeColor(LINE)
        c.setLineWidth(1)
        c.line(0, 3, self.width, 3)


# ── Score header ──────────────────────────────────────────────────────────────

class ScoreHeader(Flowable):
    def __init__(self, match_name, subtitle, score_left, score_right,
                 summary, width=W):
        super().__init__()
        self.match_name = match_name.upper()
        self.subtitle = subtitle
        self.sl, self.sr = str(score_left), str(score_right)
        self.summary = summary
        self.width = width
        self.height = 168

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        H, Wd = self.height, self.width

        # Title + subtitle
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 30)
        c.drawString(0, H - 30, self.match_name)
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 9)
        c.drawString(2, H - 46, self.subtitle.upper())

        c.setStrokeColor(LINE)
        c.setLineWidth(1)
        c.line(0, H - 60, Wd, H - 60)

        # HOME (left)
        c.setFillColor(TEAL)
        c.rect(0, 30, 6, 26, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(16, 44, 'HOME')
        c.setFillColor(TEAL)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(16, 32, 'TEAM 1')

        # AWAY (right)
        c.setFillColor(GOLD)
        c.rect(Wd - 6, 30, 6, 26, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 13)
        c.drawRightString(Wd - 16, 44, 'AWAY')
        c.setFillColor(GOLD)
        c.setFont('Helvetica-Bold', 8)
        c.drawRightString(Wd - 16, 32, 'TEAM 2')

        # FULL TIME label
        c.setFillColor(GRAY)
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(Wd / 2, 70, 'FULL TIME')

        # Score (coloured) centred
        c.setFont('Helvetica-Bold', 38)
        dash = '  -  '
        wl = c.stringWidth(self.sl, 'Helvetica-Bold', 38)
        wd = c.stringWidth(dash, 'Helvetica-Bold', 38)
        wr = c.stringWidth(self.sr, 'Helvetica-Bold', 38)
        x0 = Wd / 2 - (wl + wd + wr) / 2
        ys = 30
        c.setFillColor(TEAL)
        c.drawString(x0, ys, self.sl)
        c.setFillColor(WHITE)
        c.drawString(x0 + wl, ys, dash)
        c.setFillColor(GOLD)
        c.drawString(x0 + wl + wd, ys, self.sr)

        # Summary line
        c.setFillColor(GRAY)
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(Wd / 2, 10, self.summary.upper())


# ── Possession block (big % numbers + stacked bar) ────────────────────────────

class PossessionBlock(Flowable):
    def __init__(self, t1_pct, t2_pct, width=W):
        super().__init__()
        self.t1, self.t2, self.width = t1_pct, t2_pct, width
        self.height = 70

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        Wd = self.width
        c.setFillColor(TEAL)
        c.setFont('Helvetica-Bold', 26)
        c.drawString(0, self.height - 26, f'{self.t1:.1f}%')
        c.setFillColor(GOLD)
        c.drawRightString(Wd, self.height - 26, f'{self.t2:.1f}%')

        # stacked bar
        bar_y, bar_h = 4, 18
        total = self.t1 + self.t2 or 1
        t1w = Wd * self.t1 / total
        c.setFillColor(TRACK)
        c.roundRect(0, bar_y, Wd, bar_h, 5, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.roundRect(0, bar_y, max(2, t1w), bar_h, 5, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.roundRect(t1w, bar_y, max(2, Wd - t1w), bar_h, 5, fill=1, stroke=0)


# ── Diverging stat row (mirrored bars around a centred label) ──────────────────

class DivergingStat(Flowable):
    NUM_COL = 70
    CENTER_HALF = 82

    def __init__(self, label, disp1, disp2, frac1, frac2, width=W, show_bar=True):
        super().__init__()
        self.label = label
        self.d1, self.d2 = disp1, disp2
        self.f1, self.f2 = frac1, frac2
        self.width = width
        self.show_bar = show_bar
        self.height = 24

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        Wd, H = self.width, self.height
        cy = H / 2
        center = Wd / 2

        # numbers
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(TEAL)
        c.drawRightString(self.NUM_COL - 10, cy - 4, self.d1)
        c.setFillColor(GOLD)
        c.drawString(Wd - self.NUM_COL + 10, cy - 4, self.d2)

        # label
        c.setFillColor(GRAY)
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(center, cy - 3, self.label.upper())

        if not self.show_bar:
            return

        bar_h = 6
        by = cy - bar_h / 2
        left_end = center - self.CENTER_HALF
        right_start = center + self.CENTER_HALF
        max_len = left_end - self.NUM_COL

        lw = max_len * max(0.0, min(1.0, self.f1))
        rw = max_len * max(0.0, min(1.0, self.f2))
        if lw > 0:
            c.setFillColor(TEAL)
            c.roundRect(left_end - lw, by, lw, bar_h, 3, fill=1, stroke=0)
        if rw > 0:
            c.setFillColor(GOLD)
            c.roundRect(right_start, by, rw, bar_h, 3, fill=1, stroke=0)


# ── Set-piece cells (four across) ─────────────────────────────────────────────

class SetPieceRow(Flowable):
    def __init__(self, cells, width=W):
        # cells: list of (title, v1, v2)
        super().__init__()
        self.cells, self.width = cells, width
        self.height = 64

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        H = self.height
        n = len(self.cells)
        cw = self.width / n
        for i, (title, v1, v2) in enumerate(self.cells):
            cx = i * cw + cw / 2
            c.setFillColor(GRAY)
            c.setFont('Helvetica-Bold', 8)
            c.drawCentredString(cx, H - 14, title.upper())

            c.setFont('Helvetica-Bold', 22)
            s1, s2 = str(v1), str(v2)
            gap = '   '
            w1 = c.stringWidth(s1, 'Helvetica-Bold', 22)
            wg = c.stringWidth(gap, 'Helvetica-Bold', 22)
            w2 = c.stringWidth(s2, 'Helvetica-Bold', 22)
            x0 = cx - (w1 + wg + w2) / 2
            y = H - 46
            c.setFillColor(TEAL)
            c.drawString(x0, y, s1)
            c.setFillColor(DGRAY)
            c.drawString(x0 + w1, y, gap)
            c.setFillColor(GOLD)
            c.drawString(x0 + w1 + wg, y, s2)

            if i < n - 1:
                c.setStrokeColor(LINE)
                c.setLineWidth(0.6)
                c.line((i + 1) * cw, 8, (i + 1) * cw, H - 8)


# ── Player performance panel ──────────────────────────────────────────────────

class PlayerPanel(Flowable):
    ROW_H = 16

    def __init__(self, team_id, players, accent, max_distance, width):
        # players: list of (pid, stats_dict)
        super().__init__()
        self.team_id = team_id
        self.players = players
        self.accent = accent
        self.max_distance = max_distance or 1
        self.width = width
        self.height = 40 + len(players) * self.ROW_H + 6

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        P, H = self.width, self.height

        # header
        c.setFillColor(self.accent)
        c.rect(0, H - 16, 5, 13, fill=1, stroke=0)
        c.setFillColor(self.accent)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(12, H - 15, f'TEAM {self.team_id}')

        # column headers
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 6.5)
        c.drawString(4, H - 30, 'PLAYER')
        c.drawString(54, H - 30, 'DISTANCE')
        c.drawString(P - 96, H - 30, 'SPEED')
        c.drawRightString(P, H - 30, 'POSS')

        bx0, bx1 = 50, P - 110           # distance bar track span
        track_w = bx1 - bx0

        y = H - 44
        for pid, s in self.players:
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7.5)
            c.drawString(4, y, f'#{pid}')

            # distance bar
            c.setFillColor(TRACK)
            c.roundRect(bx0, y - 1, track_w, 5, 2, fill=1, stroke=0)
            frac = s['total_distance'] / self.max_distance
            if frac > 0:
                c.setFillColor(self.accent)
                c.roundRect(bx0, y - 1, max(2, track_w * frac), 5, 2, fill=1, stroke=0)

            c.setFillColor(WHITE)
            c.setFont('Helvetica', 7)
            c.drawString(bx1 + 4, y, f"{s['total_distance']:.0f}m")
            c.drawString(P - 96, y, f"{s['top_speed']:.1f}")
            c.drawRightString(P, y, f"{s['possession_frames'] / 24:.0f}s")
            y -= self.ROW_H


# ── AI analysis parsing ───────────────────────────────────────────────────────

def _parse_analysis(text):
    sections = {'overview': [], 'tips1': [], 'tips2': []}
    current = None
    for raw in (text or '').splitlines():
        line = raw.strip()
        if line.startswith('## '):
            h = line[3:].lower()
            if 'overview' in h:
                current = 'overview'
            elif 'team 1' in h:
                current = 'tips1'
            elif 'team 2' in h:
                current = 'tips2'
            else:
                current = None
            continue
        if current is None:
            continue
        if current == 'overview':
            sections['overview'].append(line)
        elif line:
            sections[current].append(line[2:] if line[:2] in ('- ', '* ') else line)

    # collapse overview lines into paragraphs (blank line = paragraph break)
    paras, buf = [], []
    for ln in sections['overview']:
        if ln:
            buf.append(ln)
        elif buf:
            paras.append(' '.join(buf))
            buf = []
    if buf:
        paras.append(' '.join(buf))
    sections['overview'] = paras
    return sections


def _tip_box(title, bullets, accent, col_w):
    rows = [[_p(title, size=10, font='Helvetica-Bold', color=accent)]]
    if bullets:
        for b in bullets:
            rows.append([_p(f'•&nbsp;&nbsp;{b}', size=8, color=WHITE, leading=12)])
    else:
        rows.append([_p('No tips available.', size=8, color=GRAY)])
    t = Table(rows, colWidths=[col_w])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), PANEL),
        ('LINEABOVE',     (0, 0), (-1, 0), 3, accent),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('TOPPADDING',    (0, 0), (-1, 0), 10),
        ('TOPPADDING',    (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


# ── Page furniture (background, top bar, footer) ──────────────────────────────

def _draw_canvas(c, doc):
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # top bar
    c.setFillColor(TEAL)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(L_MARGIN, PAGE_H - 42, '● FOOTBALL MATCH ANALYSIS')
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 8)
    c.drawRightString(PAGE_W - R_MARGIN, PAGE_H - 42,
                      datetime.now().strftime('%d %B %Y').upper())
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(L_MARGIN, PAGE_H - 52, PAGE_W - R_MARGIN, PAGE_H - 52)

    # footer
    c.setStrokeColor(LINE)
    c.line(L_MARGIN, 40, PAGE_W - R_MARGIN, 40)
    c.setFillColor(DGRAY)
    c.setFont('Helvetica', 7)
    c.drawCentredString(PAGE_W / 2, 28,
                        'GENERATED BY AUTOMATIC FOOTBALL ANALYSIS  ·  POWERED BY CLAUDE AI')


# ── Main PDF builder ──────────────────────────────────────────────────────────

def save_pdf(pdf_path: str, match_name: str,
             structured_data: dict, analysis_text: str):

    poss  = structured_data.get('possession', {})
    shots = structured_data.get('shots', {})
    pas   = structured_data.get('passes', {})
    form  = structured_data.get('formations', {})
    sp    = structured_data.get('set_pieces', {}) or {}
    pstats = structured_data.get('player_stats', {}) or {}

    t1_pct = poss.get('team_1_pct', 0.0)
    t2_pct = poss.get('team_2_pct', 0.0)
    g1 = shots.get('team_1_goals', 0)
    g2 = shots.get('team_2_goals', 0)

    doc = SimpleDocTemplate(
        pdf_path, pagesize=(PAGE_W, PAGE_H),
        leftMargin=L_MARGIN, rightMargin=R_MARGIN,
        topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN,
        title=f'Match Report — {match_name}',
    )
    story = []

    # ── Score header ──────────────────────────────────────────────────────────
    if g1 > g2:
        result = 'Team 1 wins'
    elif g2 > g1:
        result = 'Team 2 wins'
    else:
        result = 'Draw'
    top_poss = max(t1_pct, t2_pct)
    summary = f'{result}  ·  {top_poss:.1f}% top possession  ·  {g1 + g2} goals'
    story += [
        ScoreHeader(match_name, 'Automated computer-vision match report',
                    g1, g2, summary),
        Spacer(1, 14),
    ]

    # ── 01 Ball possession ────────────────────────────────────────────────────
    story += [
        SectionHeader('01', 'Ball Possession'),
        Spacer(1, 10),
        PossessionBlock(t1_pct, t2_pct),
        Spacer(1, 18),
    ]

    # ── 02 Shots & passing (diverging bars) ───────────────────────────────────
    def frac(a, b):
        m = max(a, b)
        return (a / m if m else 0.0, b / m if m else 0.0)

    rows = [
        ('Goals',        g1, g2, str(g1), str(g2)),
        ('Shots',        shots.get('team_1_shots', 0), shots.get('team_2_shots', 0), None, None),
        ('On Target',    shots.get('team_1_on_target', 0), shots.get('team_2_on_target', 0), None, None),
        ('Off Target',   shots.get('team_1_off_target', 0), shots.get('team_2_off_target', 0), None, None),
        ('Passes',       pas.get('team_1_passes', 0), pas.get('team_2_passes', 0), None, None),
        ('Turnovers',    pas.get('team_1_turnovers', 0), pas.get('team_2_turnovers', 0), None, None),
        ('Pass Accuracy', pas.get('team_1_accuracy', 0.0), pas.get('team_2_accuracy', 0.0),
                         f"{pas.get('team_1_accuracy', 0.0):.1f}%", f"{pas.get('team_2_accuracy', 0.0):.1f}%"),
        ('Total Distance', pas.get('team_1_total_distance', 0.0), pas.get('team_2_total_distance', 0.0),
                         f"{pas.get('team_1_total_distance', 0.0):.0f}", f"{pas.get('team_2_total_distance', 0.0):.0f}"),
        ('Sprints',      pas.get('team_1_sprints', 0), pas.get('team_2_sprints', 0), None, None),
    ]

    story += [SectionHeader('02', 'Shots & Passing'), Spacer(1, 8)]
    for label, v1, v2, d1, d2, *_ in [(r[0], r[1], r[2], r[3], r[4]) for r in rows]:
        f1, f2 = frac(v1, v2)
        story += [
            DivergingStat(label, d1 if d1 is not None else str(v1),
                          d2 if d2 is not None else str(v2), f1, f2),
            Spacer(1, 4),
        ]
    # formation row (text, no bars)
    story += [
        DivergingStat('Formation', form.get('team_1_formation', '?'),
                      form.get('team_2_formation', '?'), 0, 0, show_bar=False),
        Spacer(1, 16),
    ]

    # ── 03 Set pieces ─────────────────────────────────────────────────────────
    story += [
        SectionHeader('03', 'Set Pieces'),
        Spacer(1, 10),
        SetPieceRow([
            ('Corners',   sp.get('team_1_corners', 0),    sp.get('team_2_corners', 0)),
            ('Throw-ins', sp.get('team_1_throw_ins', 0),  sp.get('team_2_throw_ins', 0)),
            ('Free Kicks', sp.get('team_1_free_kicks', 0), sp.get('team_2_free_kicks', 0)),
            ('Penalties', sp.get('team_1_penalties', 0),  sp.get('team_2_penalties', 0)),
        ]),
        Spacer(1, 18),
    ]

    # ── 04 Player performance ─────────────────────────────────────────────────
    def team_players(tid):
        ps = [(pid, s) for pid, s in pstats.items() if s.get('team') == tid
              and (s.get('total_distance', 0) > 0 or s.get('possession_frames', 0) > 0)]
        return sorted(ps, key=lambda x: x[1].get('total_distance', 0), reverse=True)[:11]

    p1, p2 = team_players(1), team_players(2)
    max_dist = max([s['total_distance'] for _, s in p1 + p2] + [1])
    col_w = (W - 16) / 2

    story += [SectionHeader('04', 'Player Performance'), Spacer(1, 10)]
    if p1 or p2:
        panels = Table(
            [[PlayerPanel(1, p1, TEAL, max_dist, col_w),
              PlayerPanel(2, p2, GOLD, max_dist, col_w)]],
            colWidths=[col_w + 8, col_w + 8])
        panels.setStyle(TableStyle([
            ('LEFTPADDING',  (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 16),
            ('LEFTPADDING',  (1, 0), (1, 0), 16),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(panels)
    else:
        story.append(_p('No player data available.', size=9, color=GRAY))
    story.append(Spacer(1, 18))

    # ── 05 AI match analysis ──────────────────────────────────────────────────
    sections = _parse_analysis(analysis_text)
    story += [SectionHeader('05', 'AI Match Analysis'), Spacer(1, 10)]

    story.append(_p('MATCH OVERVIEW', size=9, font='Helvetica-Bold', color=TEAL))
    story.append(Spacer(1, 4))
    if sections['overview']:
        for para in sections['overview']:
            story.append(_p(para, size=8.5, color=colors.HexColor('#C2CBD4'),
                            leading=13, space_after=6))
    else:
        story.append(_p('No analysis available.', size=9, color=GRAY))
    story.append(Spacer(1, 8))

    tip_w = (W - 16) / 2
    tips = Table(
        [[_tip_box('TIPS FOR TEAM 1', sections['tips1'], TEAL, tip_w),
          _tip_box('TIPS FOR TEAM 2', sections['tips2'], GOLD, tip_w)]],
        colWidths=[tip_w + 8, tip_w + 8])
    tips.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 16),
        ('LEFTPADDING',  (1, 0), (1, 0), 16),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tips)

    doc.build(story, onFirstPage=_draw_canvas, onLaterPages=_draw_canvas)
    print(f'[PDFReporter] Report saved to {pdf_path}')
