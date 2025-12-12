from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pptx import Presentation
from PIL import Image
import io
import os
import subprocess
import shutil
import tempfile

app = FastAPI(title="DeckLint Renderer V2", version="2.0.0")

@app.get("/health")
def health_check():
    # Check if libreoffice is available
    libreoffice_status = shutil.which("libreoffice") is not None
    return {"status": "ok", "libreoffice_installed": libreoffice_status}

@app.post("/render/slide")
async def render_slide(
    slide_index: int = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Create temp dir
        with tempfile.TemporaryDirectory() as tmpdirname:
            pptx_path = os.path.join(tmpdirname, "input.pptx")
            pdf_path = os.path.join(tmpdirname, "input.pdf")
            
            # Save upload
            with open(pptx_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Convert to PDF using LibreOffice
            # --headless --convert-to pdf --outdir <dir> <file>
            cmd = [
                "libreoffice", "--headless", "--convert-to", "pdf", 
                "--outdir", tmpdirname, pptx_path
            ]
            
            # Timeout set to 30s to prevent hanging
            subprocess.run(cmd, check=True, timeout=30)
            
            if not os.path.exists(pdf_path):
                raise HTTPException(status_code=500, detail="PDF conversion failed (no output)")
            
            # Convert PDF page to Image (using poppler / pdftoppm)
            # For this 'pixel perfect' request, we really want an image of the specific page.
            # subprocess pdftoppm -png -f <page> -l <page> <pdf> <prefix>
            # slide_index is 0-based, pdftoppm uses 1-based
            page_num = slide_index + 1
            
            img_prefix = os.path.join(tmpdirname, "slide")
            cmd_img = [
                "pdftoppm", "-png", "-f", str(page_num), "-l", str(page_num), 
                pdf_path, img_prefix
            ]
            subprocess.run(cmd_img, check=True, timeout=10)
            
            # find the output file (pdftoppm adds -1.png or similar suffix)
            # actually usually adds -01.png or just nothing if single page? 
            # pdftoppm naming is tricky. Let's list dir
            files = os.listdir(tmpdirname)
            png_file = next((f for f in files if f.endswith(".png")), None)
            
            if not png_file:
                 raise HTTPException(status_code=500, detail="Image conversion failed")
                 
            with open(os.path.join(tmpdirname, png_file), "rb") as f:
                img_content = f.read()

            return Response(content=img_content, media_type="image/png")

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Rendering subprocess failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
