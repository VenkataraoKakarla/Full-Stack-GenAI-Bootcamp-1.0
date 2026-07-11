import json
from pathlib import Path

nb_path = Path(r"D:\Full-Stack-GenAI-Bootcamp-1.0\Class-30-Data-Parsing-for-RAG\data_parsing_part2.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))

new_source = '''# ============================================================
# 2. Parse PDF using Docling
# ============================================================

from docling.document_converter import DocumentConverter

# Initialize variables up front so later cells always have a safe state.
docling_doc = None
markdown_text = ""

try:
    converter = DocumentConverter()

    # Convert PDF into Docling structured document
    conversion_result = converter.convert(PDF_PATH)

    # Main Docling document object
    docling_doc = getattr(conversion_result, "document", None)

    if docling_doc is not None and hasattr(docling_doc, "export_to_markdown"):
        markdown_text = docling_doc.export_to_markdown()
        print("Docling conversion completed.")
    else:
        raise ValueError("Docling returned no usable document object.")

except Exception as e:
    print("Docling conversion failed:", repr(e))
    print("Falling back to PyMuPDF text extraction for continued notebook execution.")

    import fitz

    doc = fitz.open(PDF_PATH)
    page_texts = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        page_texts.append(f"## Page {page_num}\\n{text}")

    markdown_text = "\\n\\n".join(page_texts)
    docling_doc = None

print("Markdown ready for export.")
'''

updated = False
for cell in nb.get("cells", []):
    if cell.get("cell_type") == "code":
        src = "".join(cell.get("source", []))
        if "from docling.document_converter import DocumentConverter" in src and "# 2. Parse PDF using Docling" in src:
            cell["source"] = new_source.splitlines(keepends=True)
            updated = True
            break

if not updated:
    raise SystemExit("Target cell not found")

nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Updated {nb_path}")
