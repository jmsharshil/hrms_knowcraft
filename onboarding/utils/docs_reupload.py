from django.db.models import FileField

def get_pending_documents(docs):
    """
    Returns a list of document field names that are not approved
    """
    pending_docs = []
    for field in docs._meta.get_fields():
        if isinstance(field, FileField):
            file_name = field.name
            approved_field = f"{file_name}_approved"

            if hasattr(docs, approved_field):
                file_value = getattr(docs, file_name)
                approved_value = getattr(docs, approved_field)

                if file_value and not approved_value:
                    pending_docs.append(
                        file_name.replace('_', ' ').title()
                    )
    return pending_docs