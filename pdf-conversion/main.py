import pypdf
from markdownify import markdownify

pdf_path = 'test.pdf'

# Open the PDF file
with open(pdf_path, 'rb') as file:
    reader = pypdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

# Optionally format the text into Markdown using markdownify
markdown_text = markdownify(text)

# Save to a .md file
with open('output.md', 'w') as output_file:
    output_file.write(markdown_text)

print("Markdown file generated successfully!")
