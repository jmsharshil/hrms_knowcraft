def get_pending_documents(docs):
    """
    Returns a list of document field names that are not approved
    """
    pending_docs = []
    for field in docs._meta.get_fields():
        if field.name.endswith('_approved'):
            if not getattr(docs, field.name):
                original_field = field.name.replace('_approved', '')
                pending_docs.append(original_field.replace('_', ' ').title())
    return pending_docs