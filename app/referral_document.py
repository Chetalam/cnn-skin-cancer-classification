"""Readable Word export from an existing owned prediction, without inference."""
from io import BytesIO
from datetime import datetime, timezone

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from translations import t
from classification_info import CLASS_INFO, ABOUT, WHY, GENERAL_ONLY, LIMIT, CLOSED_SET, SOURCES, interpretation


def checklist_docx(prediction):
    # Shared validation keeps text and Word exports bound to the same saved result.
    from referral import checklist_text, NOTICE, SCC_LIMITATION, STEPS, HANDOVER, FIELDS
    checklist_text(prediction)
    clean = lambda value: ' '.join(str(value).split())
    doc = Document()
    for border in list(doc.styles.element.iter(qn("w:pBdr"))):
        border.getparent().remove(border)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.top_margin = sec.bottom_margin = Inches(.7)
    sec.left_margin = sec.right_margin = Inches(.8)
    for style in ['Normal', 'Title', 'Heading 1', 'Heading 2']:
        doc.styles[style].font.name = 'Calibri'
        doc.styles[style].font.color.rgb = RGBColor(0, 0, 0)
    normal = doc.styles['Normal']
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(8)
    doc.styles['Title'].font.size = Pt(23)
    doc.styles['Heading 1'].font.size = Pt(15)
    doc.styles['Heading 1'].paragraph_format.space_before = Pt(12)
    doc.styles['Heading 1'].paragraph_format.space_after = Pt(7)
    doc.add_paragraph(t('Clinical assessment and referral checklist'), 'Title')
    doc.add_paragraph(t('Decision support only'))
    doc.add_heading(t('Prediction summary'), 1)
    saved = datetime.fromtimestamp(prediction['created_at'], timezone.utc).strftime('%d %b %Y, %H:%M UTC')
    for label, value in [('Review ID', prediction['image_id']), ('Case reference', clean(prediction.get('case_reference') or '—')),
                         ('Prediction saved', saved), ('Predicted class', prediction['cancer_class']),
                         ('Model score', f"{prediction['confidence']:.1%}")]:
        p = doc.add_paragraph()
        p.add_run(t(label) + ': ').bold = True
        p.add_run(str(value))
        p.paragraph_format.space_after = Pt(3)
    p = doc.add_paragraph()
    p.add_run(t('Model version') + ': ').bold = True
    # A separate wrap opportunity prevents long SHA strings pushing table widths.
    p.add_run(clean(prediction['model_name']))
    p.paragraph_format.space_after = Pt(8)
    doc.add_heading(t('All class scores'), 1)
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Light Shading Accent 1'
    table.cell(0, 0).text, table.cell(0, 1).text = t('Class'), t('Score')
    for label in ('BCC', 'Melanoma', 'SCC'):
        cells = table.add_row().cells
        cells[0].text, cells[1].text = label, f"{prediction['scores'][label]:.1%}"
    for row in table.rows:
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.space_before = Pt(4)
    doc.add_heading(t(ABOUT), 1)
    name, description, signs = CLASS_INFO[prediction['cancer_class']]
    doc.add_paragraph(t(name) + '. ' + t(description))
    doc.add_paragraph(t(signs))
    doc.add_paragraph(t(GENERAL_ONLY))
    doc.add_heading(t(WHY), 1)
    doc.add_paragraph(interpretation(prediction))
    doc.add_paragraph(t(LIMIT))
    doc.add_paragraph(t(CLOSED_SET))
    doc.add_page_break()
    doc.add_heading(t('Referral and follow up'), 1)
    doc.add_paragraph(t(NOTICE))
    doc.add_paragraph(t(SCC_LIMITATION))
    for n, step in enumerate(STEPS, 1):
        p = doc.add_paragraph()
        p.add_run(str(n) + '. ').bold = True
        p.add_run(t(step))
        p.paragraph_format.space_after = Pt(12)
    doc.add_heading(t(HANDOVER), 1)
    for field in FIELDS:
        p = doc.add_paragraph()
        p.add_run(t(field)).bold = True
        p = doc.add_paragraph('________________________________________________________________')
        p.paragraph_format.space_after = Pt(12)
    doc.add_heading(t('Educational sources'), 1)
    for title, url in SOURCES:
        p = doc.add_paragraph(title + '\n' + url)
        p.paragraph_format.space_after = Pt(5)
        for run in p.runs:
            run.font.size = Pt(9)
    doc.core_properties.author = ''
    doc.core_properties.title = 'Clinical assessment and referral checklist'
    doc.core_properties.subject = 'Saved model output and clinical handover'
    output = BytesIO()
    doc.save(output)
    return output.getvalue()
