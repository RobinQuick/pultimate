import magic
from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE = 50 * 1024 * 1024 # 50 MB
ALLOWED_MIME_TYPES = [
    "application/vnd.openxmlformats-officedocument.presentationml.presentation", # .pptx
    "application/vnd.openxmlformats-officedocument.presentationml.template",     # .potx
]

async def validate_pptx_file(file: UploadFile):
    # 1. Size Check
    # Note: Content-Length header is not always reliable or present. 
    # Ideally, we stream and count, but for V1 simple validation:
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max size is {MAX_FILE_SIZE/1024/1024}MB")

    # 2. Magic Check
    # Read header bytes
    header = file.file.read(2048)
    file.file.seek(0)
    
    mime = magic.from_buffer(header, mime=True)
    
    # Python-magic might identify pptx as 'application/zip' because it is a zip.
    # We must allow zip but verifying structure is expensive here (requires unzip).
    # Strict PPTX mime usually requires deep inspection.
    # For now, allow zip and office types.
    if mime not in ALLOWED_MIME_TYPES and mime != "application/zip":
         # Extended check logic could go here
         raise HTTPException(status_code=400, detail=f"Invalid file type: {mime}. Only .pptx allowed.")

    return True
