from ollama_client import generate


def summarize(text):

    print("Longitud del texto:", len(text))

    prompt = f"""
Resume el siguiente texto en puntos claros y organizados.

TEXTO: 
{text[:2000]}
"""
    return generate(prompt)
