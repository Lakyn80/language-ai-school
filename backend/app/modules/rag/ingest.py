import json
from pathlib import Path
from app.modules.rag.vectorstore import VectorStore


TITLES_PATH = Path(__file__).parents[2] / "modules" / "titles" / "data" / "titles.json"


def ingest_titles():
    with open(TITLES_PATH, encoding="utf-8") as f:
        data = json.load(f)

    texts = []
    metadatas = []

    for title in data["titles"]:
        text = f"""
        {title['name']}
        Universe: {title['universe']}
        Level: {title['level']}
        Description: {title['description']}
        """

        texts.append(text)
        metadatas.append(title)

    store = VectorStore()
    store.build(texts, metadatas)

    print("✅ Titles ingested into FAISS")


if __name__ == "__main__":
    ingest_titles()
