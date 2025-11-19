from azure.storage.blob import BlobServiceClient
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

def upload_docs_to_storage(candidate,file_obj):
    media_url = None
    try:
        file_bytes = file_obj.read()
    except Exception as e:
        logger.error("Failed to read file_obj: %s", e, exc_info=True)
        return None
    filename = f"{candidate.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    if settings.USE_AZURE_MEDIA:
        try:
            # Step 3: Upload to Azure Blob Storage
            connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER)

            try:
                container_client.get_container_properties()  # This will raise if not found
                logger.info(f"✅ Container '{settings.AZURE_CONTAINER}' exists.")
            except Exception as e:
                logger.info(f"📦 Creating container '{settings.AZURE_CONTAINER}'...")
                container_client.create_container()
                logger.info(f"✅ Container '{settings.AZURE_CONTAINER}' created successfully.")

            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(file_bytes, overwrite=True)
            media_url = f"https://{settings.AZURE_CUSTOM_DOMAIN}/{settings.AZURE_CONTAINER}/{filename}"
        except Exception as e:
            print(e)
    else:
        try:
            fs = FileSystemStorage()
            saved_name = fs.save(filename, file_obj)
            media_url =f"{settings.BASE_URL}{fs.url(saved_name)}"
        except Exception as e:
            print(e)

    return media_url