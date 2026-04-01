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
clean_html = markdown.markdown(
    executive_summary,
    extensions=['tables', 'fenced_code', 'nl2br'],
    output_format='html5'
)

# ====== Write to  file
with open('executive_summary.pdf', 'w') as f:
    f.write(clean_html)

# ====== Complete the script execution
print("Executive summary HTML generated: executive_summary.html")