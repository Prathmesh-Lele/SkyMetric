"""Convert markdown documentation to PDF using Playwright."""

import markdown
import asyncio
from playwright.async_api import async_playwright

# Read markdown
with open("skymetric_documentation.md", "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to HTML
html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

# Full HTML with styling
html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
        max-width: 750px;
        margin: 0 auto;
        padding: 20px;
    }
    h1 {
        color: #1a1a2e;
        font-size: 24pt;
        text-align: center;
        border-bottom: 3px solid #16213e;
        padding-bottom: 10px;
        margin-top: 30px;
        page-break-before: always;
    }
    h1:first-of-type {
        page-break-before: avoid;
    }
    h2 {
        color: #16213e;
        font-size: 16pt;
        margin-top: 30px;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
        page-break-after: avoid;
    }
    h3 {
        color: #0f3460;
        font-size: 13pt;
        margin-top: 20px;
        page-break-after: avoid;
    }
    h4 {
        color: #1a1a2e;
        font-size: 11pt;
        margin-top: 15px;
        page-break-after: avoid;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 9.5pt;
        page-break-inside: avoid;
    }
    th {
        background-color: #16213e;
        color: white;
        padding: 8px;
        text-align: left;
        font-size: 9pt;
    }
    td {
        padding: 6px 8px;
        border-bottom: 1px solid #ddd;
    }
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 5px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
    }
    pre {
        background-color: #1a1a2e;
        color: #e0e0e0;
        padding: 12px;
        border-radius: 5px;
        overflow-x: auto;
        font-size: 8.5pt;
        line-height: 1.3;
        page-break-inside: avoid;
    }
    pre code {
        background-color: transparent;
        color: #e0e0e0;
    }
    strong {
        color: #1a1a2e;
    }
    hr {
        border: none;
        border-top: 2px solid #16213e;
        margin: 25px 0;
    }
    ul, ol {
        margin: 8px 0;
        padding-left: 22px;
    }
    li {
        margin: 3px 0;
    }
    p {
        margin: 8px 0;
    }
</style>
</head>
<body>
""" + html_body + """
</body>
</html>"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(
            path="SkyMetric_Documentation.pdf",
            format="A4",
            margin={"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"},
            print_background=True,
        )
        await browser.close()
        print("PDF generated successfully: SkyMetric_Documentation.pdf")

asyncio.run(main())
