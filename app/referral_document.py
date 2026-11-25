"""Readable Word export from an existing owned prediction, without inference."""
from io import BytesIO
from datetime import datetime, timezone

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from translations import t
from branding import PROJECT_NAME, SHORT_NAME
from explainability import (
    validate_explanation, LIMITATION,
    COLOUR_GUIDE_TITLE, COLOUR_GUIDE_INTRO, COLOUR_GUIDE_RED,
    COLOUR_GUIDE_BLUE, COLOUR_GUIDE_STRENGTH,
    COLOUR_GUIDE_EXAMPLE, COLOUR_GUIDE_CAUTION,
)
from classification_info import CLASS_INFO, ABOUT, WHY, GENERAL_ONLY, LIMIT, CLOSED_SET, interpretation


def checklist_docx(prediction, explanation=None):
    # Shared validation keeps text and Word exports bound to the same saved result.
    from referral import checklist_text, NOTICE, SCC_LIMITATION, STEPS, HANDOVER, FIELDS
    checklist_text(prediction)
    if explanation is not None:
        validate_explanation(explanation, prediction)
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
    doc.add_paragraph(SHORT_NAME)
    doc.add_paragraph(t('Decision support only'))
    footer = sec.footer.paragraphs[0]
    footer.add_run(SHORT_NAME + '  |  ' + t('Review ID') + ': ' + str(prediction['image_id']) + '  |  ')
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    for run in footer.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string('506879')
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
    if prediction.get('preview_sha256'):
        doc.add_paragraph(t('Prediction used the saved preview.'))
    doc.add_heading(t('All class scores'), 1)
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    borders = OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        border = OxmlElement('w:' + edge)
        for key, value in [('val','single'),('sz','4'),('color','D9D9D9')]:
            border.set(qn('w:' + key), value)
        borders.append(border)
    table._tbl.tblPr.append(borders)
    table.cell(0, 0).text, table.cell(0, 1).text = t('Class'), t('Score')
    for label in ('BCC', 'Melanoma', 'SCC'):
        cells = table.add_row().cells
        cells[0].text, cells[1].text = label, f"{prediction['scores'][label]:.1%}"
    for cell in table.rows[0].cells:
        shade = OxmlElement('w:shd')
        shade.set(qn('w:fill'), 'DDEFF1')
        cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs:
            run.bold = True
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
    doc.add_page_break()
    doc.add_heading(t(WHY), 1)
    doc.add_paragraph(interpretation(prediction))
    doc.add_paragraph(t(LIMIT))
    doc.add_paragraph(t(CLOSED_SET))
    doc.add_heading(t('Referral and follow up'), 1)
    doc.add_paragraph(t(NOTICE))
    doc.add_paragraph(t(SCC_LIMITATION))
    for n, step in enumerate(STEPS, 1):
        p = doc.add_paragraph()
        p.add_run(str(n) + '. ').bold = True
        p.add_run(t(step))
        p.paragraph_format.space_after = Pt(12)
    doc.add_page_break()
    doc.add_heading(t(HANDOVER), 1)
    for field in FIELDS:
        p = doc.add_paragraph()
        p.add_run(t(field)).bold = True
        p = doc.add_paragraph('________________________________________________________________')
        p.paragraph_format.space_after = Pt(12)
    if explanation is not None:
        doc.add_page_break()
        doc.add_heading(t('Visual explanation'), 1)
        doc.add_paragraph(t('Regions affecting the predicted-class score') + ': ' + prediction['cancer_class'])
        doc.add_paragraph(t(COLOUR_GUIDE_INTRO))
        doc.add_picture(BytesIO(explanation['overlay']), width=Inches(3.8))
        doc.add_heading(t(COLOUR_GUIDE_TITLE), 2)
        for guide in (COLOUR_GUIDE_RED, COLOUR_GUIDE_BLUE, COLOUR_GUIDE_STRENGTH):
            paragraph = doc.add_paragraph(t(guide), style='List Bullet')
            paragraph.paragraph_format.space_after = Pt(5)
        doc.add_paragraph(t(COLOUR_GUIDE_EXAMPLE))
        important = doc.add_paragraph()
        important.add_run(t(COLOUR_GUIDE_CAUTION)).bold = True
        doc.add_paragraph(t('Largest score decrease') + ': ' + f"{max(0, explanation['regions'][0]['drop_pp']):.2f} pp")
        doc.add_paragraph(t('Largest score increase') + ': ' + f"{max(0, -explanation['regions'][-1]['drop_pp']):.2f} pp")
        doc.add_paragraph(t('pp means percentage points, not a change in cancer risk.'))
        doc.add_paragraph(t(LIMITATION))
        doc.add_paragraph(explanation['method'])
        doc.add_paragraph('https://captum.ai/api/occlusion.html')
    doc.core_properties.author = PROJECT_NAME
    doc.core_properties.title = 'Clinical assessment and referral checklist'
    doc.core_properties.subject = PROJECT_NAME
    output = BytesIO()
    doc.save(output)
    return output.getvalue()
