"""
An exploratory run of the OneVizion API on APPS2.
Author: David
Email: ddemand@onevizion.com
Date: 3/27/2026
"""

# ====== Import the required modules
import json
import io
import pandas as pd
import requests
import os
from openai import OpenAI
import markdown
import re
from html import escape
from reportlab.platypus import Image

# ====== Set variables and other environmental items
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# ====== Get API key's
def get_api_key(api_name):
    file_path = "/Users/daviddemand/PyCharmMiscProject/api_keys/api_creds.json"
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            for api in data['api_keys']:
                if api['api_name'] == api_name:
                    return api['api_key']
            print(f"No API key found for '{api_name}'")
            return None
    except FileNotFoundError:
        print(f"Error: API keys file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in API keys file")
        return None
    except Exception as e:
        print(f"Error reading API keys: {e}")
        return None


# ====== Get API key's
apps2_api_key = get_api_key("apps2_api_key")
if not apps2_api_key:
    raise Exception("API key not found. Exiting.")

azure_foundry_api_key = get_api_key("azure_foundry")
if not azure_foundry_api_key:
    raise Exception("API key not found. Exiting.")

# ====== Get the data
BASE_URL = 'https://apps2.onevizion.com/api/v3/trackor/1002067287/file/RR_RR_FILE'

headers = {"Authorization": apps2_api_key,
           "Accept": "text/csv"}

response = requests.get(BASE_URL, headers=headers)
response.raise_for_status()

csv_text = response.content.decode("utf-8-sig")  # handles BOM
df = pd.read_csv(io.StringIO(csv_text))

# ====== If we added a chunk here, we could write to PostgreSQL periodically and append the data to build a pipeline.
# df.to_....

# ====== Use an AI model to analyze the data (Instance name: 'apps2-azure-analysis')
endpoint = "https://ddemand.openai.azure.com/openai/v1/"
deployment_name = "gpt-4.1"

client = OpenAI(
    base_url=endpoint,
    api_key=azure_foundry_api_key
)

analysis_prompt = f"""
You are an expert Program Director overseeing projects in the telecom industry for large network deployments, and the 
construction of wireless and fiber optic networks.

Analyze this project data carefully. 
Data (JSON):
{df.to_dict(orient="records")}

Focus on:
- Group by: 'Program ID', 'Project Type' and 'Project Priority'
- Overall Project Health: 'Schedule Status', budget variances, resource bottlenecks
- Risks: timeline slips ('On-Air to Baseline Variance'), cost overruns, permitting/location issues
- Responsibilities: 'Program Manager', 'Project Manager', 'Construction Manager', 'Commissioning Manager', 
'General Contractor', 'Next Milestone Responsible Person'
- Insights: strategic recommendations for scaling nationwide backhaul

Output format — use markdown-style headings:

Summary Details

Overall Program Health Status

- Bullet points...

Key Projects Overview and Milestones

...

Risks & Mitigations

...

Strategic Recommendations

Be concise, professional, data-driven, and actionable. Identify any responsible parties to assign actionable items to.
Use bold text to bring attention to critical items. 
"""

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {"role": "user",
         "content": analysis_prompt,
        }
    ],
)

print(completion.choices[0].message)

# ====== Assemble the executive reporting
executive_summary = completion.choices[0].message.content.strip()


def md_to_reportlab(text: str) -> str:
    """
    Converts **bold** markdown to ReportLab-safe <b> tags
    and escapes everything else.
    """
    if not text:
        return ""

    # Escape everything first
    text = escape(text)

    # Replace markdown bold **text**
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text
    )

    return text


from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from datetime import datetime

# ===== PDF file name
pdf_filename = "Executive_Project_Summary.pdf"

# ===== Document setup
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=LETTER,
    rightMargin=50,
    leftMargin=50,
    topMargin=50,
    bottomMargin=50
)

# ===== Styles
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="TitleStyle",
    fontSize=18,
    leading=22,
    spaceAfter=16,
    textColor=HexColor("#2c3e50"),
    alignment=TA_LEFT
))

styles.add(ParagraphStyle(
    name="HeaderStyle",
    fontSize=13,
    leading=16,
    spaceBefore=16,
    spaceAfter=8,
    textColor=HexColor("#2c3e50"),
    fontName="Helvetica-Bold"
))

styles.add(ParagraphStyle(
    name="BodyStyle",
    fontSize=10.5,
    leading=14,
    spaceAfter=6
))

styles.add(ParagraphStyle(
    name="BulletStyle",
    fontSize=10.5,
    leading=14,
    leftIndent=12
))

styles.add(ParagraphStyle(
    name="H1",
    fontSize=16,
    leading=20,
    spaceBefore=20,
    spaceAfter=10,
    fontName="Helvetica-Bold",
    textColor=HexColor("#2c3e50")
))

styles.add(ParagraphStyle(
    name="H2",
    fontSize=14,
    leading=18,
    spaceBefore=18,
    spaceAfter=8,
    fontName="Helvetica-Bold",
    textColor=HexColor("#2c3e50")
))

styles.add(ParagraphStyle(
    name="H3",
    fontSize=12.5,
    leading=16,
    spaceBefore=16,
    spaceAfter=6,
    fontName="Helvetica-Bold",
    textColor=HexColor("#34495e")
))

# ===== Content container
elements = []

# ===== Add logo at top of document
logo_path = "assets/logo.png"

if os.path.exists(logo_path):
    logo = Image(
        logo_path,
        width=2.44 * inch,   # adjust if needed
        height=0.49 * inch,
        hAlign="LEFT"
    )
    elements.append(logo)
    elements.append(Spacer(1, 0.25 * inch))

# ===== Title Section
elements.append(Paragraph("Executive Project Summary", styles["TitleStyle"]))
elements.append(Paragraph(
    "<b>Program:</b> Telecom Network Deployment<br/>"
    f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
    styles["BodyStyle"]
))
elements.append(Spacer(1, 0.3 * inch))

# ===== Parse Markdown-like structure
markdown_lines = executive_summary.splitlines()
bullet_buffer = []

for line in markdown_lines:
    raw_line = line.strip()

    if not raw_line:
        continue

    # ===== Markdown Headings (#, ##, ###)
    if raw_line.startswith("#"):
        if bullet_buffer:
            elements.append(ListFlowable(
                [ListItem(Paragraph(b, styles["BulletStyle"])) for b in bullet_buffer],
                bulletType="bullet"
            ))
            bullet_buffer = []

        level = len(raw_line) - len(raw_line.lstrip("#"))
        text = raw_line.lstrip("#").strip()

        if level == 1:
            elements.append(Paragraph(md_to_reportlab(text), styles["H1"]))
        elif level == 2:
            elements.append(Paragraph(md_to_reportlab(text), styles["H2"]))
        else:
            elements.append(Paragraph(md_to_reportlab(text), styles["H3"]))

        continue

    # ===== Bullet points
    if raw_line.startswith("-"):
        bullet_buffer.append(md_to_reportlab(raw_line.lstrip("- ").strip()))
        continue

    # ===== Normal paragraph
    if bullet_buffer:
        elements.append(ListFlowable(
            [ListItem(Paragraph(b, styles["BulletStyle"])) for b in bullet_buffer],
            bulletType="bullet"
        ))
        bullet_buffer = []

    elements.append(Paragraph(md_to_reportlab(raw_line), styles["BodyStyle"]))

# Flush remaining bullets
if bullet_buffer:
    elements.append(ListFlowable(
        [ListItem(Paragraph(b, styles["BulletStyle"])) for b in bullet_buffer],
        bulletType="bullet"
    ))

# Flush remaining bullets
if bullet_buffer:
    elements.append(ListFlowable(
        [ListItem(Paragraph(b, styles["BulletStyle"])) for b in bullet_buffer],
        bulletType="bullet"
    ))

# ===== Build PDF
doc.build(elements)
print(f"✅ Professional PDF generated: {pdf_filename}")