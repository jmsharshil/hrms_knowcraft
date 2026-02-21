def get_annexure_attachment(docs):
    annexure_attachment = None

    if docs.salary_annexure:
        try:
            docs.salary_annexure.open()
            file_content = docs.salary_annexure.read()
            filename = docs.salary_annexure.name.split("/")[-1]

            annexure_attachment = (
                filename,
                file_content,
                "application/pdf"  # or detect dynamically
            )
            docs.salary_annexure.close()

        except Exception as e:
            print("Resume fetch error:", e)

    return annexure_attachment        
