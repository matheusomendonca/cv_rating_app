import os
import pdfplumber
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4

class CVParser:
    """Parse PDF CVs and return a list of dicts with file name, unique id, and raw text."""

    def __init__(self, source_path: str):
        self.source_path = source_path

    def _pdf_files(self) -> List[str]:
        if os.path.isdir(self.source_path):
            return [
                os.path.join(self.source_path, f)
                for f in os.listdir(self.source_path)
                if f.lower().endswith(".pdf")
            ]
        if self.source_path.lower().endswith(".pdf"):
            return [self.source_path]
        raise ValueError("Provided path must be a directory or a PDF file.")

    def _parse_single_pdf(self, fpath: str) -> Dict:
        """Parse a single PDF file."""
        try:
            with pdfplumber.open(fpath) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            return {
                "file": os.path.basename(fpath),
                "candidate_id": str(uuid4()),
                "content": text,
            }
        except Exception as e:
            # Return error info for failed parsing
            return {
                "file": os.path.basename(fpath),
                "candidate_id": str(uuid4()),
                "content": f"Error parsing PDF: {str(e)}",
                "error": True
            }

    def parse(self, max_workers: int = 8) -> List[Dict]:
        """Parse PDF files in parallel."""
        pdf_files = self._pdf_files()
        parsed: List[Dict] = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(self._parse_single_pdf, fpath): fpath for fpath in pdf_files}
            
            for fut in as_completed(futures):
                try:
                    result = fut.result()
                    parsed.append(result)
                except Exception as e:
                    fpath = futures[fut]
                    parsed.append({
                        "file": os.path.basename(fpath),
                        "candidate_id": str(uuid4()),
                        "content": f"Error parsing PDF: {str(e)}",
                        "error": True
                    })
        
        return parsed
