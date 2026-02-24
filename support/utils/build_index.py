import os
from django.conf import settings
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# from support.utils.vector_storage import download_kb_files, upload_vector_files

import tempfile
from azure.storage.blob import BlobServiceClient
load_dotenv()
settings.configure()

CONNECTION_STRING = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={os.getenv("AZURE_ACCOUNT_NAME")};"
    f"AccountKey={os.getenv("AZURE_ACCOUNT_KEY")};"
    f"EndpointSuffix=core.windows.net"
)

CONTAINER_NAME = "media"
VECTOR_FOLDER = "kb"


def get_blob_service():
    return BlobServiceClient.from_connection_string(CONNECTION_STRING)


def upload_vector_files(faiss_path, meta_path, index_name="support_index"):

    blob_service = get_blob_service()
    container = blob_service.get_container_client(CONTAINER_NAME)

    faiss_blob = f"{VECTOR_FOLDER}/{index_name}.faiss"
    meta_blob = f"{VECTOR_FOLDER}/{index_name}.pkl"

    with open(faiss_path, "rb") as f:
        container.upload_blob(faiss_blob, f, overwrite=True)

    with open(meta_path, "rb") as f:
        container.upload_blob(meta_blob, f, overwrite=True)

def download_kb_files():

    blob_service = get_blob_service()
    container = blob_service.get_container_client(CONTAINER_NAME)

    blobs = container.list_blobs(name_starts_with="kb/")

    temp_dir = tempfile.mkdtemp()
    file_paths = []

    for blob in blobs:

        if not blob.name.endswith(".txt"):
            continue

        local_path = os.path.join(temp_dir, os.path.basename(blob.name))

        with open(local_path, "wb") as f:
            data = container.download_blob(blob.name).readall()
            f.write(data)

        file_paths.append(local_path)

    return file_paths

def download_vector_files(index_name="support_index"):

    blob_service = get_blob_service()
    container = blob_service.get_container_client(CONTAINER_NAME)

    faiss_blob = f"{VECTOR_FOLDER}/{index_name}.faiss"
    meta_blob = f"{VECTOR_FOLDER}/{index_name}.pkl"

    temp_dir = tempfile.mkdtemp()

    faiss_path = os.path.join(temp_dir, "index.faiss")
    meta_path = os.path.join(temp_dir, "index.pkl")

    with open(faiss_path, "wb") as f:
        f.write(container.download_blob(faiss_blob).readall())

    with open(meta_path, "wb") as f:
        f.write(container.download_blob(meta_blob).readall())

    return faiss_path, meta_path

def build_vector_from_all_kbs(index_name="support_index"):

    print("⬇ Downloading KB files from Azure...")

    kb_files = download_kb_files()  # returns local file paths

    combined_text = ""

    for file_path in kb_files:
        with open(file_path, "r", encoding="utf-8") as f:
            combined_text += f.read() + "\n\n"

    print("✂ Splitting text...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    docs = splitter.create_documents([combined_text])

    print("🧠 Creating embeddings...")

    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("ENDPOINT_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        api_version="2024-05-01-preview",
        azure_deployment="text-embedding-3-large"
    )

    vectorstore = FAISS.from_documents(docs, embeddings)

    temp_dir = "temp_vector"
    os.makedirs(temp_dir, exist_ok=True)

    vectorstore.save_local(temp_dir)

    faiss_path = os.path.join(temp_dir, "index.faiss")
    meta_path = os.path.join(temp_dir, "index.pkl")

    print("⬆ Uploading vector DB to Azure...")

    upload_vector_files(faiss_path, meta_path, index_name)

    print("✅ Vector DB created successfully!")


if __name__ == "__main__":
    build_vector_from_all_kbs()