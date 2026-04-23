from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

# ── Colour palette ───────────────────────────────────────────────────────────
NAVY   = colors.HexColor('#1B2A4A')
GREEN  = colors.HexColor('#27AE60')
BLUE   = colors.HexColor('#2980B9')
GOLD   = colors.HexColor('#F39C12')
LGRAY  = colors.HexColor('#F2F3F4')
MGRAY  = colors.HexColor('#BDC3C7')
DARK   = colors.HexColor('#2C3E50')
LGREEN = colors.HexColor('#EAF7EE')
LBLUE  = colors.HexColor('#EAF3FB')
WHITE  = colors.white


# ── Custom flowables ─────────────────────────────────────────────────────────

class PossessionBar(Flowable):
    """Horizontal stacked bar showing possession split."""
    def __init__(self, t1_pct, t2_pct, width, height=34):
        super().__init__()
        self.t1_pct = t1_pct
        self.t2_pct = t2_pct
        self.width = width
        self.height = height

    def wrap(self, *args):
        return self.width, self.height

    def draw(self):
        c = self.canv
        t1_w = self.width * self.t1_pct / 100

        c.setFillColor(GREEN)
        c.roundRect(0, 0, t1_w, self.height, 4, fill=1, stroke=0)

        c.setFillColor(BLUE)
        c.roundRect(t1_w, 0, self.width - t1_w, self.height, 4, fill=1, stroke=0)

        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 10)
        if self.t1_pct >= 12:
            c.drawString(10, 12, f'Team 1   {self.t1_pct:.1f}%')
        if self.t2_pct >= 12:
            c.drawRightString(self.width - 10, 12, f'{self.t2_pct:.1f}%   Team 2')


# ── Paragraph helpers ─────────────────────────────────────────────────────────

def _p(text, **kw):
    return Paragraph(text, ParagraphStyle('_', **kw))

def _hp(text):
    """White bold header cell paragraph."""
    return _p(text, fontSize=9, fontName='Helvetica-Bold',
              textColor=WHITE, alignment=TA_CENTER)

def _cp(text):
    """Centered body paragraph."""
    return _p(text, fontSize=9, fontName='Helvetica', textColor=DARK, alignment=TA_CENTER)

def _lp(text, bold=False):
    """Left-aligned body paragraph."""
    return _p(text, fontSize=9,
              fontName='Helvetica-Bold' if bold else 'Helvetica',
              textColor=DARK, alignment=TA_LEFT)

def _empty():
    """Empty paragraph used as spacer inside table cells."""
    return _p('', fontSize=4)


# ── Section label ─────────────────────────────────────────────────────────────

def _section(text, W):
    t = Table(
        [[_p(text, fontSize=11, fontName='Helvetica-Bold', textColor=WHITE)]],
        colWidths=[W]
    )
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return t


# ── Main PDF builder ──────────────────────────────────────────────────────────

def save_pdf(pdf_path: str, match_name: str,
             structured_data: dict, analysis_text: str):

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    W = doc.width
    story = []

    # ── HEADER ───────────────────────────────────────────────────────────────
    hdr = Table([
        [_p('⚽  FOOTBALL MATCH ANALYSIS', fontSize=22, fontName='Helvetica-Bold',
            textColor=WHITE, alignment=TA_CENTER)],
        [_p(match_name, fontSize=11, fontName='Helvetica',
            textColor=colors.HexColor('#BDC3C7'), alignment=TA_CENTER)],
        [_p(datetime.now().strftime('%d %B %Y'), fontSize=9, fontName='Helvetica',
            textColor=colors.HexColor('#95A5A6'), alignment=TA_CENTER)],
    ], colWidths=[W])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NAVY),
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
    ]))
    story += [hdr, Spacer(1, 12)]

    # ── KEY METRIC CARDS ─────────────────────────────────────────────────────
    poss  = structured_data.get('possession', {})
    shots = structured_data.get('shots', {})
    pas   = structured_data.get('passes', {})
    form  = structured_data.get('formations', {})

    def card(value, label, accent):
        t = Table([
            [_p(str(value), fontSize=22, fontName='Helvetica-Bold',
                textColor=accent, alignment=TA_CENTER)],
            [_p(label, fontSize=8, fontName='Helvetica',
                textColor=colors.HexColor('#7F8C8D'), alignment=TA_CENTER)],
        ], colWidths=[W / 4 - 6])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), WHITE),
            ('BOX',           (0, 0), (-1, -1), 1, MGRAY),
            ('LINEABOVE',     (0, 0), (-1,  0), 4, accent),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        return t

    total_shots = shots.get('team_1_shots', 0) + shots.get('team_2_shots', 0)
    cards = Table([[
        card(f"{poss.get('team_1_pct', 0):.1f}%", 'Team 1 Possession', GREEN),
        card(f"{poss.get('team_2_pct', 0):.1f}%", 'Team 2 Possession', BLUE),
        card(total_shots, 'Total Shots', GOLD),
        card(pas.get('total_passes', 0), 'Total Passes', NAVY),
    ]], colWidths=[W / 4] * 4)
    cards.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story += [cards, Spacer(1, 12)]

    # ── POSSESSION BAR ───────────────────────────────────────────────────────
    story += [
        _section('BALL POSSESSION', W),
        Spacer(1, 7),
        PossessionBar(poss.get('team_1_pct', 50), poss.get('team_2_pct', 50), W),
        Spacer(1, 12),
    ]

    # ── SHOTS & PASSING TABLE ────────────────────────────────────────────────
    story += [_section('SHOTS & PASSING', W), Spacer(1, 7)]

    cw = [W * 0.44, W * 0.28, W * 0.28]
    comp = Table([
        [_hp('Metric'),          _hp('Team 1'),  _hp('Team 2')],
        [_lp('Shots', True),     _cp(str(shots.get('team_1_shots', 0))),        _cp(str(shots.get('team_2_shots', 0)))],
        [_lp('  On Target'),     _cp(str(shots.get('team_1_on_target', 0))),    _cp(str(shots.get('team_2_on_target', 0)))],
        [_lp('  Off Target'),    _cp(str(shots.get('team_1_off_target', 0))),   _cp(str(shots.get('team_2_off_target', 0)))],
        [_lp('Passes', True),    _cp(str(pas.get('team_1_passes', 0))),         _cp(str(pas.get('team_2_passes', 0)))],
        [_lp('Turnovers'),       _cp(str(pas.get('team_1_turnovers', 0))),      _cp(str(pas.get('team_2_turnovers', 0)))],
        [_lp('Pass Accuracy'),   _cp(f"{pas.get('team_1_accuracy', 0):.1f}%"),  _cp(f"{pas.get('team_2_accuracy', 0):.1f}%")],
        [_lp('Formation'),       _cp(form.get('team_1_formation', '?')),        _cp(form.get('team_2_formation', '?'))],
        [_lp('Total Distance', True),
                                 _cp(f"{pas.get('team_1_total_distance', 0):.0f} m"),
                                 _cp(f"{pas.get('team_2_total_distance', 0):.0f} m")],
        [_lp('Sprints (>25 km/h)'),
                                 _cp(str(pas.get('team_1_sprints', 0))),
                                 _cp(str(pas.get('team_2_sprints', 0)))],
    ], colWidths=cw)
    comp.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LGRAY]),
        ('GRID',          (0, 0), (-1, -1), 0.5, MGRAY),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (0, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story += [comp, Spacer(1, 12)]

    # ── PLAYER PERFORMANCE ───────────────────────────────────────────────────
    player_stats = structured_data.get('player_stats', {})
    if player_stats:
        story += [_section('PLAYER PERFORMANCE', W), Spacer(1, 7)]

        pw = [W * 0.18, W * 0.28, W * 0.28, W * 0.26]
        for team_id in [1, 2]:
            team_players = {pid: s for pid, s in player_stats.items()
                            if s.get('team') == team_id}
            if not team_players:
                continue

            accent = GREEN if team_id == 1 else BLUE
            bg     = LGREEN if team_id == 1 else LBLUE

            story.append(_p(f'Team {team_id}', fontSize=10, fontName='Helvetica-Bold',
                            textColor=NAVY, spaceBefore=4, spaceAfter=3))

            rows = [[_hp('Player'), _hp('Distance (m)'), _hp('Top Speed'), _hp('Poss. (s)')]]
            active_players = [
                (pid, s) for pid, s in team_players.items()
                if s['total_distance'] > 0 or s['possession_frames'] > 0
            ]
            top_players = sorted(active_players,
                                 key=lambda x: x[1]['total_distance'], reverse=True)[:11]
            for pid, s in top_players:
                rows.append([
                    _lp(f'#{pid}'),
                    _cp(f"{s['total_distance']:.0f}"),
                    _cp(f"{s['top_speed']:.1f} km/h"),
                    _cp(f"{s['possession_frames'] / 24:.1f}"),
                ])

            pt = Table(rows, colWidths=pw)
            pt.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0), accent),
                ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, bg]),
                ('GRID',          (0, 0), (-1, -1), 0.5, MGRAY),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING',   (0, 0), (0, -1), 8),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story += [pt, Spacer(1, 7)]

    # ── AI ANALYSIS ──────────────────────────────────────────────────────────
    story += [_section('AI MATCH ANALYSIS  (powered by Claude)', W), Spacer(1, 7)]

    analysis_rows = []
    for line in analysis_text.splitlines():
        line = line.strip()
        if not line:
            analysis_rows.append([_empty()])
        elif line.startswith('## '):
            analysis_rows.append([_p(line[3:], fontSize=11, fontName='Helvetica-Bold',
                                     textColor=GREEN)])
        elif line.startswith('- ') or line.startswith('* '):
            analysis_rows.append([_p(f'• {line[2:]}', fontSize=9, fontName='Helvetica',
                                     textColor=DARK, leftIndent=14, leading=14)])
        else:
            analysis_rows.append([_p(line, fontSize=9, fontName='Helvetica',
                                     textColor=DARK, leading=14)])

    if analysis_rows:
        at = Table(analysis_rows, colWidths=[W])
        at.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
            ('BOX',           (0, 0), (-1, -1), 1, MGRAY),
            ('LEFTPADDING',   (0, 0), (-1, -1), 12),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING',    (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ]))
        story.append(at)

    doc.build(story)
    print(f'[PDFReporter] Report saved to {pdf_path}')
