from fpdf import FPDF
import datetime
import os

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(CORE_DIR, 'NotoSansBengali-Regular.ttf')

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the Unicode font right away.
        # We'll use this for ALL text (English and Bengali)
        try:
            self.add_font('NotoSans', '', FONT_PATH, uni=True)
            self.font_added = True
            print("Successfully loaded Unicode font.")
        except RuntimeError as e:
            print(f"Warning: Could not load Unicode font NotoSansBengali-Regular.ttf. {e}")
            self.font_added = False

    def header(self):
        if self.font_added:
            self.set_font('NotoSans', '', 12)
        else:
            self.set_font('Arial', 'B', 12)
        
        self.cell(0, 10, 'Policy Analysis Report', 0, 1, 'C')
        
        if self.font_added:
            self.set_font('NotoSans', '', 8)
        else:
            self.set_font('Arial', '', 8)
        self.cell(0, 5, f'Generated on: {datetime.date.today()}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        if self.font_added:
            self.set_font('NotoSans', '', 8)
        else:
            self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_section(self, title, content):
        # Set font for title
        if self.font_added:
            self.set_font('NotoSans', '', 13) # A bit larger for title
        else:
            self.set_font('Arial', 'B', 12)
        
        self.cell(0, 10, title, 0, 1, 'L')
        
        # Set font for content
        if self.font_added:
            self.set_font('NotoSans', '', 10)
        else:
            self.set_font('Arial', '', 10)
            # Clean text if we're using the default font
            content = content.encode('latin-1', 'replace').decode('latin-1')
            
        self.multi_cell(0, 5, content)
        self.ln(5)

def create_report(analysis_data):
    pdf = PDF()
    
    # Clean all text if Unicode font is not available
    if not pdf.font_added:
        print("Warning: Unicode font not found. Cleaning text for PDF.")
        for key in ['url', 'overall_risk', 'summary', 'translated_summary']:
            if key in analysis_data and isinstance(analysis_data[key], str):
                analysis_data[key] = analysis_data[key].encode('latin-1', 'replace').decode('latin-1')
        
        if 'highlights' in analysis_data:
            analysis_data['highlights'] = [
                s.encode('latin-1', 'replace').decode('latin-1') for s in analysis_data['highlights']
            ]

    pdf.add_page()
    
    # 1. URL and Risk
    if pdf.font_added:
        pdf.set_font('NotoSans', '', 14)
    else:
        pdf.set_font('Arial', 'B', 14)
    pdf.multi_cell(0, 10, f"Analysis for: {analysis_data['url']}")
    
    if pdf.font_added:
        pdf.set_font('NotoSans', '', 16)
    else:
        pdf.set_font('Arial', 'B', 16)
        
    if analysis_data['overall_risk'] == 'High Risk':
        pdf.set_text_color(220, 50, 50) # Red
    elif analysis_data['overall_risk'] == 'Medium Risk':
        pdf.set_text_color(255, 193, 7) # Yellow-ish
    else:
        pdf.set_text_color(40, 167, 69) # Green
    pdf.cell(0, 10, f"Overall Risk: {analysis_data['overall_risk']}", 0, 1)
    pdf.set_text_color(0, 0, 0) # Reset color
    pdf.ln(5)
    
    # 2. Summary (English)
    pdf.add_section('Easy-to-Read Summary (English)', analysis_data['summary'])
    
    # 3. Translated Summary
    lang_name = analysis_data['language'].capitalize()
    pdf.add_section(f'Summary ({lang_name})', analysis_data['translated_summary'])
    
    # 4. Key Highlights
    pdf.add_section('Key Highlights & Risks', '\n'.join(analysis_data['highlights']))
    
    # Return the PDF as bytes
    return bytes(pdf.output(dest='S'))