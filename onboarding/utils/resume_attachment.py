def get_resume_attachment(candidate):
    resume_attachment = None

    if candidate.resume:
        try:
            candidate.resume.open()
            file_content = candidate.resume.read()
            filename = candidate.resume.name.split("/")[-1]

            resume_attachment = (
                filename,
                file_content,
                "application/pdf"  # or detect dynamically
            )
            print(resume_attachment)
            candidate.resume.close()

        except Exception as e:
            print("Resume fetch error:", e)

    return resume_attachment        
