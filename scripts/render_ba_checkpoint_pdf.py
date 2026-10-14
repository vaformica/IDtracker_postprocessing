"""Render the BA checkpoint Markdown as a linked, readable PDF."""
import html
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'reports/BA_SCIENTIFIC_DATA_CHECKPOINT_2026-10-14.md'
OUTPUT = ROOT/'output/pdf/BA_SCIENTIFIC_DATA_CHECKPOINT_2026-10-14.pdf'


def inline(text):
    text = text.replace('—', ' - ').replace('–', '-').replace('’', "'").replace('“', '"').replace('”', '"')
    text = html.escape(text)
    def link(m):
        label, target = m.group(1), html.unescape(m.group(2))
        if not target.startswith(('https://', 'http://')):
            target = (SOURCE.parent/target).resolve().as_uri()
        return '<a href="'+html.escape(target, quote=True)+'" color="#075d99">'+label+'</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" size="8.5">\1</font>', text)
    return text


def render():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyBA', fontName='Helvetica', fontSize=10, leading=13.2,
                              spaceAfter=7, textColor=colors.HexColor('#20313b')))
    styles.add(ParagraphStyle(name='CellBA', parent=styles['BodyBA'], fontSize=8.8, leading=12,
                              spaceAfter=0, splitLongWords=True))
    styles['Heading1'].fontSize = 23; styles['Heading1'].leading = 27
    styles['Heading1'].textColor = colors.HexColor('#183e4a')
    styles['Heading2'].fontSize = 14; styles['Heading2'].leading = 18
    styles['Heading2'].spaceBefore = 14; styles['Heading2'].spaceAfter = 8
    styles['Heading2'].textColor = colors.HexColor('#183e4a')
    story = []; lines = SOURCE.read_text().splitlines(); i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', c) for c in cells):
                    rows.append([Paragraph(inline(c), styles['CellBA']) for c in cells])
                i += 1
            table = Table(rows, colWidths=[121, 131, 264], repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eff2')),
                ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),7),
                ('RIGHTPADDING',(0,0),(-1,-1),7), ('TOPPADDING',(0,0),(-1,-1),7),
                ('BOTTOMPADDING',(0,0),(-1,-1),7),
                ('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor('#cbd7db'))]))
            story.extend([table, Spacer(1,10)]); continue
        if line.startswith('# '): style = styles['Heading1']; line = line[2:]
        elif line.startswith('## '): style = styles['Heading2']; line = line[3:]
        else: style = styles['BodyBA']
        if line.startswith('- '): line = '&#8226; '+inline(line[2:])
        else: line = inline(line)
        story.append(Paragraph(line, style)); i += 1
    def page(canvas, doc):
        canvas.setStrokeColor(colors.HexColor('#cbd7db'));canvas.line(48,42,564,42)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526974'))
        canvas.drawString(48,29,'BA scientific data checkpoint | 14 October 2026 | Prepared by Codex')
        canvas.drawRightString(564,29,str(doc.page))
    SimpleDocTemplate(str(OUTPUT), pagesize=(612,792), leftMargin=48,rightMargin=48,
        topMargin=45,bottomMargin=55,title='BA scientific data checkpoint - 14 October 2026',
        author='Codex; human QC decisions by VAF').build(story,onFirstPage=page,onLaterPages=page)
    print(OUTPUT)


if __name__ == '__main__': render()
