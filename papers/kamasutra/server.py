
import os, uuid, glob

from fastapi import FastAPI, UploadFile, File, HTTPException, Form

from fastapi.responses import PlainTextResponse

import torch

from transformers import AutoModel, AutoTokenizer



MODEL = "deepseek-ai/DeepSeek-OCR-2"

tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)

model = AutoModel.from_pretrained(

    MODEL,

    _attn_implementation="flash_attention_2",   # change to "sdpa" if flash-attn isn't installed

    trust_remote_code=True,

    use_safetensors=True,

).eval().cuda().to(torch.bfloat16)



PROMPTS = {

    "markdown": "<image>\n<|grounding|>Convert the document to markdown. ",

    "free":     "<image>\nFree OCR. ",

}



WORK = "/tmp/ocr"; os.makedirs(WORK, exist_ok=True)

app = FastAPI()



@app.get("/health")

def health(): return {"ok": True}



@app.post("/ocr", response_class=PlainTextResponse)

async def ocr(file: UploadFile = File(...),

              mode: str = Form("markdown"),

              base_size: int = Form(1024),

              image_size: int = Form(768),

              crop_mode: bool = Form(True)):

    if mode not in PROMPTS:

        raise HTTPException(400, "mode must be 'markdown' or 'free'")

    job = uuid.uuid4().hex

    img = os.path.join(WORK, f"{job}.png")

    out = os.path.join(WORK, job); os.makedirs(out, exist_ok=True)

    with open(img, "wb") as f: f.write(await file.read())



    text = model.infer(

        tokenizer,

        prompt=PROMPTS[mode],

        image_file=img,

        output_path=out,

        base_size=base_size,

        image_size=image_size,

        crop_mode=crop_mode,

        save_results=True,

    )

    if isinstance(text, str) and text.strip():

        return text

    # fall back to whatever the model wrote to disk

    for ext in ("*.mmd", "*.md", "*.txt"):

        hits = glob.glob(os.path.join(out, ext))

        if hits: return open(hits[0]).read()

    raise HTTPException(500, "no output produced")

