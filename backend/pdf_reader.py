from pypdf import PdfReader


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() + "/n"

    print("Longitud de texto: ", len(text))
    print(text[:500])

    return text
