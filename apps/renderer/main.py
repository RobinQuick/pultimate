from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pptx import Presentation
from PIL import Image, ImageDraw, ImageFont
import io
import math

app = FastAPI(title="DeckLint Renderer", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/render/slide")
async def render_slide(
    slide_index: int = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Load PPTX from bytes
        content = await file.read()
        prs = Presentation(io.BytesIO(content))
        
        if slide_index < 0 or slide_index >= len(prs.slides):
            raise HTTPException(status_code=400, detail="Slide index out of range")
            
        slide = prs.slides[slide_index]
        
        # Create a placeholder image (1920x1080)
        img = Image.new('RGB', (1920, 1080), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        # attempt to draw text boxes as best effort
        # This is a "Proof of Processing", not high fidelity
        for shape in slide.shapes:
            if shape.has_text_frame:
                 # Simple heuristic for position
                 left = int(shape.left.inches * 96) # very rough conversion
                 top = int(shape.top.inches * 96)
                 text = shape.text_frame.text[:50] # truncated
                 d.text((left, top), text, fill=(0,0,0))
                 d.rectangle([left, top, left+100, top+20], outline="blue")

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diff")
async def diff_images(
    img1: UploadFile = File(...),
    img2: UploadFile = File(...)
):
    # Placeholder diff logic
    # In real app, load images, pixel diff, return score and diff image
    return {"score": 1.0, "diff_url": "placeholder"}
