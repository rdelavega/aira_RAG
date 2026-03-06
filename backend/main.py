from pdf_reader import extract_text
from summarizer import summarize
import os

PDF_PATH = "../data/RodrigoDelaVega_CV_es.pdf"


def run():

    print("Leyendo PDF...")
    text = extract_text(PDF_PATH)

    print("Generando resumen con IA...")
    summary = summarize(text)

    os.makedirs("../summaries", exist_ok=True)

    with open("../summaries/book_summary.md", "w") as f:
        f.write("# Resumen del libro\n\n")
        f.write(summary)

    print("Resumen guardado.")


if __name__ == "__main__":
    run()
