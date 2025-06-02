import streamlit as st
import pdfplumber
import docx
import pandas as pd
import re
import spacy
from io import BytesIO
nlp = spacy.load("en_core_web_sm")

#File Readers
def read_txt(file): return file.read().decode('utf-8')
def read_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

#Attribute Extractor
def extract_attributes(text):
    lines = text.split('\n')
    products = []
    for line in lines:
        doc = nlp(line)
        brand = next((token.text for token in doc if token.pos_ == "PROPN"), "")
        processor = re.search(r'\bi[3579]\b', line)
        ram = re.search(r'\b\d{1,2}GB RAM\b', line, re.IGNORECASE)
        storage = re.search(r'\d+GB SSD|\d+TB HDD|\d+GB HDD', line, re.IGNORECASE)
        price = re.search(r'\$\d+', line)
        if any([brand, processor, ram, storage, price]):
            products.append({
                "Brand": brand,
                "Processor": processor.group(0) if processor else "",
                "RAM": ram.group(0) if ram else "",
                "Storage": storage.group(0) if storage else "",
                "Price": price.group(0) if price else "",
                "Raw Line": line
            })
    return pd.DataFrame(products)
# ===== Streamlit UI =====
st.set_page_config(page_title="AI Attribute Extractor", layout="centered")
st.title("🧠 AI Product Attribute Extractor")
uploaded_file = st.file_uploader("📁 Upload a .txt, .pdf, or .docx file", type=["txt", "pdf", "docx"])
if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")
    ext = uploaded_file.name.split('.')[-1]
    if ext == "txt":
        text = read_txt(uploaded_file)
    elif ext == "pdf":
        text = read_pdf(uploaded_file)
    elif ext == "docx":
        text = read_docx(uploaded_file)
    else:
        st.error("Unsupported file format.")
        st.stop()
    st.subheader("Extracted Text")
    st.text_area("Preview", text[:1000], height=200)
    df = extract_attributes(text)
    if df.empty:
        st.warning("No product attributes detected.")
    else:
        st.subheader("Extracted Product Attributes")
        st.dataframe(df)

        # Excel download
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("Download Excel Summary", data=output.getvalue(),
                           file_name="summary_output.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
