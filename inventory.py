import csv
import re


def normalize_text(text):
    text = text.lower().strip()

    replacements = {
        "pulgada y media": "1-1/2",
        "una pulgada y media": "1-1/2",
        "uno y medio": "1-1/2",
        "1 1/2": "1-1/2",
        "1.5": "1-1/2",

        "media": "1/2",
        "medio": "1/2",

        "tres cuartos": "3/4",

        "ch20": "ch 20",
        "ch18": "ch 18",
        "ch16": "ch 16",
        "ch14": "ch 14",

        "chapa 20": "ch 20",
        "chapa 18": "ch 18",
        "chapa 16": "ch 16",
        "chapa 14": "ch 14",

        "calibre 20": "ch 20",
        "calibre 18": "ch 18",
        "calibre 16": "ch 16",
        "calibre 14": "ch 14",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def tokenize(text):
    text = normalize_text(text)
    return re.findall(r"\d+-\d+/\d+|\d+/\d+|\d+x\d+|\d+|[a-záéíóúñ]+", text)


def calculate_score(row, query_tokens):
    score = 0

    searchable_fields = {
        "medida_normalizada": 30,
        "grueso": 25,
        "familia": 15,
        "forma": 12,
        "acabado": 10,
        "categoria": 8,
        "aliases": 20,
    }

    for field, weight in searchable_fields.items():
        field_tokens = tokenize(row.get(field, ""))

        for token in query_tokens:
            if token in field_tokens:
                score += weight

    return score


def search_product(query):
    results = []
    query_tokens = tokenize(query)

    with open("backend/Products.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            score = calculate_score(row, query_tokens)

            if score > 0:
                row["score"] = score
                results.append(row)

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results