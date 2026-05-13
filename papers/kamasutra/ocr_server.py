#!/usr/bin/env python
"""OCR server for DeepSeek-OCR-2.

Returns JSON with text + per-region bounding box data.

Endpoints:
    POST /ocr  — OCR an image
    GET /health — health check

Usage:
    python ocr_server.py
    python ocr_server.py --port 8000
"""

import os
import sys
import re
import uuid
import glob
import json
import argparse
from io import StringIO

import torch
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from transformers import AutoModel, AutoTokenizer

MODEL_NAME = "deepseek-ai/DeepSeek-OCR-2"
WORK = "/tmp/ocr"

PROMPTS = {
    "markdown": "<image>\n<|grounding|>Convert the document to markdown. ",
    "free":     "<image>\nFree OCR. ",
}

app = FastAPI()
model = None
tokenizer = None


# ── Bounding box parsing ────────────────────────────────────────────────────

# The model outputs <|ref|>text<|/ref|><|det|>[[x1,y1,x2,y2]]<|/det|>
# followed by OCR text for that region.

_BBOX_RE = re.compile(
    r"<\|ref\|>(.*?)<\|/ref\|>"
    r"<\|det\|>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|/det\|>"
)


def parse_boxes(raw_output: str) -> list[dict]:
    matches = list(_BBOX_RE.finditer(raw_output))
    if not matches:
        return []

    boxes = []
    for idx, m in enumerate(matches):
        ref_text = m.group(1)
        x1, y1, x2, y2 = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        text_start = m.end()
        text_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_output)
        ocr_text = raw_output[text_start:text_end].strip()
        boxes.append({
            "bbox": [x1, y1, x2, y2],
            "ref_text": ref_text.strip(),
            "ocr_text": ocr_text,
        })
    return boxes


def clean_debug_output(text: str) -> str:
    """Remove model debug lines that leak into stdout."""
    # Lines that are clearly model internals, not OCR output
    debug_prefixes = (
        "BASE:", "PATCHES:", "image:", "other:",
        "===============save results",
        "=====================",
        "The attention mask",
        "Setting `pad_token_id`",
        "`get_max_cache()`",
        "The attention layers",
        "The `seen_tokens`",
    )
    lines = text.split("\n")
    kept = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue
        if any(stripped.startswith(p) for p in debug_prefixes):
            continue
        if stripped.startswith("`") and "is deprecated" in stripped:
            continue
        kept.append(line)
    return "\n".join(kept)


def extract_clean_text(raw_output: str) -> str:
    return clean_debug_output(_BBOX_RE.sub("", raw_output)).strip()


def detect_language(text: str) -> str:
    deva = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    total = deva + latin
    if total == 0:
        return "unknown"
    if deva / max(total, 1) > 0.7:
        return "devanagari"
    if latin / max(total, 1) > 0.7:
        return "latin"
    return "mixed"


def build_response(raw_text: str, page_size: tuple | None = None) -> dict:
    raw_text = clean_debug_output(raw_text)
    boxes = parse_boxes(raw_text)
    clean_text = extract_clean_text(raw_text)

    regions = []
    for box in boxes:
        text = box["ocr_text"]
        if not text:
            continue
        regions.append({
            "bbox": box["bbox"],
            "text": text,
            "language": detect_language(text),
            "ref_text": box["ref_text"],
        })

    total_deva = sum(
        sum(1 for c in r["text"] if 0x0900 <= ord(c) <= 0x097F)
        for r in regions
    )
    total_latin = sum(
        sum(1 for c in r["text"] if c.isascii() and c.isalpha())
        for r in regions
    )

    response = {
        "text": clean_text,
        "page": {
            "num_regions": len(regions),
            "total_chars": sum(len(r["text"]) for r in regions),
            "devanagari_chars": total_deva,
            "latin_chars": total_latin,
            "dominant_language": detect_language(clean_text),
        },
        "regions": regions,
    }
    if page_size:
        response["page"]["width"] = page_size[0]
        response["page"]["height"] = page_size[1]
    return response


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    mode: str = Form("markdown"),
    base_size: int = Form(1024),
    image_size: int = Form(768),
    crop_mode: bool = Form(True),
):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if mode not in PROMPTS:
        raise HTTPException(status_code=400, detail="mode must be 'markdown' or 'free'")

    # Save uploaded image to temp
    job = uuid.uuid4().hex
    img_path = os.path.join(WORK, f"{job}.png")
    out_dir = os.path.join(WORK, job)
    os.makedirs(out_dir, exist_ok=True)
    # Also ensure WORK exists
    os.makedirs(WORK, exist_ok=True)

    contents = await file.read()
    with open(img_path, "wb") as f:
        f.write(contents)

    try:
        from PIL import Image
        from io import BytesIO
        img = Image.open(BytesIO(contents))
        page_size = img.size
    except Exception:
        page_size = None

    # Run inference — capture stdout to get the raw output with bbox tokens.
    # model.infer() prints the full output (with <|ref|>/<|det|> tokens) to
    # stdout, then returns a cleaned version. We capture both.
    old_stdout = sys.stdout
    sys.stdout = captured = StringIO()
    try:
        text = model.infer(
            tokenizer,
            prompt=PROMPTS[mode],
            image_file=img_path,
            output_path=out_dir,
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode,
            save_results=True,
        )
    finally:
        sys.stdout = old_stdout

    raw_stdout = captured.getvalue()

    if not isinstance(text, str) or not text.strip():
        # Fall back to saved files on disk
        for ext in ("*.mmd", "*.md", "*.txt"):
            hits = glob.glob(os.path.join(out_dir, ext))
            if hits:
                text = open(hits[0], encoding="utf-8").read()
                break
        else:
            text = ""

    # Prefer the raw stdout (has bbox tokens) over the return value (cleaned).
    # Fall back through return value, saved files, raw stdout — whichever is richest.
    candidates = [raw_stdout, text]
    for ext in ("*.mmd", "*.md", "*.txt"):
        for hit in sorted(glob.glob(os.path.join(out_dir, ext))):
            candidates.append(open(hit, encoding="utf-8").read())

    # Pick the candidate with the most bbox tokens, then longest text
    def bbox_score(s):
        return (len(_BBOX_RE.findall(s)), len(s))

    full_text = max(candidates, key=bbox_score) if candidates else ""

    if not full_text.strip():
        raise HTTPException(status_code=500, detail="No output produced")

    # Build structured response with bounding boxes
    response = build_response(full_text, page_size)

    # Cleanup temp files
    try:
        import shutil
        shutil.rmtree(out_dir, ignore_errors=True)
        os.remove(img_path)
    except Exception:
        pass

    return response


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DeepSeek-OCR-2 server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    print(f"Loading model: {MODEL_NAME}")
    global model, tokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        MODEL_NAME,
        _attn_implementation="flash_attention_2",
        trust_remote_code=True,
        use_safetensors=True,
    ).eval().cuda().to(torch.bfloat16)

    os.makedirs(WORK, exist_ok=True)
    print(f"Model loaded. Starting server on {args.host}:{args.port}")

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
