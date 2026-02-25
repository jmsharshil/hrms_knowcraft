import os
import tempfile
from azure.storage.blob import BlobServiceClient
from django.conf import settings

CONNECTION_STRING = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={settings.AZURE_ACCOUNT_NAME};"
    f"AccountKey={settings.AZURE_ACCOUNT_KEY};"
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