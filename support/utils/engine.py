import os
import tempfile
from django.conf import settings

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from .vector_storage import download_vector_files


_db = None


def load_db():
    global _db

    if _db:
        return _db

    # ⭐ Download from Azure instead of local
    faiss_path, meta_path = download_vector_files("support_index")

    embeddings = OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY,
        model="text-embedding-3-large"
    )

    folder = os.path.dirname(faiss_path)

    _db = FAISS.load_local(
        folder,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return _db

def retrieve_context(question, k=4):

    db = load_db()

    docs_with_scores = db.similarity_search_with_score(question, k=k)

    if not docs_with_scores:
        return "LOW_CONFIDENCE"

    best_score = docs_with_scores[0][1]

    # lower score = better match
    if best_score > 2:
        return "LOW_CONFIDENCE"

    context = "\n\n".join([doc.page_content for doc, _ in docs_with_scores])

    return context