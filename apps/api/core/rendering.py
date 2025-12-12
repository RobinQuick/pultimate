import subprocess
import os
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

LIBREOFFICE_TIMEOUT = 30 # seconds
PDFTOPPM_TIMEOUT = 10 # seconds

async def convert_pptx_to_pdf(pptx_path: str, output_dir: str) -> Optional[str]:
    """
    Converts PPTX to PDF using LibreOffice headless.
    Returns path to generated PDF or None if failed.
    """
    cmd = [
        "libreoffice", "--headless", "--convert-to", "pdf",
        "--outdir", output_dir, pptx_path
    ]
    
    try:
        # Run in thread executor to avoid blocking async loop since subprocess.run is blocking
        # Or use asyncio.create_subprocess_exec for true async
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=LIBREOFFICE_TIMEOUT)
        except asyncio.TimeoutError:
            process.kill()
            logger.error(f"LibreOffice conversion timed out after {LIBREOFFICE_TIMEOUT}s")
            return None

        if process.returncode != 0:
            logger.error(f"LibreOffice failed: {stderr.decode()}")
            return None
            
        # Filename inference: LO keeps basename and changes ext to pdf
        base = os.path.splitext(os.path.basename(pptx_path))[0]
        pdf_path = os.path.join(output_dir, f"{base}.pdf")
        
        if os.path.exists(pdf_path):
            return pdf_path
        return None
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return None

async def convert_pdf_to_png(pdf_path: str, output_dir: str, page_num: int = 1) -> Optional[bytes]:
    """
    Converts specific page of PDF to PNG bytes using pdftoppm.
    page_num is 1-based.
    """
    # Prefix for output
    img_prefix = os.path.join(output_dir, f"slide_{page_num}")
    
    cmd = [
        "pdftoppm", "-png", "-f", str(page_num), "-l", str(page_num),
        pdf_path, img_prefix
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
             await asyncio.wait_for(process.communicate(), timeout=PDFTOPPM_TIMEOUT)
        except asyncio.TimeoutError:
            process.kill()
            logger.error(f"pdftoppm timed out after {PDFTOPPM_TIMEOUT}s")
            return None
            
        if process.returncode != 0:
            logger.error("pdftoppm failed")
            return None
            
        # pdftoppm appends -1.png or -01.png depending on version/count.
        # simpler to just read the file generated.
        # It usually generates {prefix}-1.png if single page requested?
        # Let's find the file
        expected_name = f"{img_prefix}-{page_num}.png" # Default format often
        # Validating actual filename requires listing dir or knowing pdftoppm version quirks.
        # Robust way: list dir matching prefix
        
        files = os.listdir(output_dir)
        # Filter for files starting with slide_{page_num} and ending .png
        target_file = next((f for f in files if f.startswith(f"slide_{page_num}") and f.endswith(".png")), None)
        
        if target_file:
            with open(os.path.join(output_dir, target_file), "rb") as f:
                return f.read()
                
        return None
        
    except Exception as e:
        logger.error(f"PNG conversion error: {e}")
        return None
