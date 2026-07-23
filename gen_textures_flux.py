#!/usr/bin/env python3
"""Generate seamless gym textures via local ComfyUI + FLUX.1 schnell (fp8 all-in-one).
Free, local. Stdlib only."""
import json, time, urllib.request, urllib.error, shutil, os

HOST = "http://127.0.0.1:8188"
CKPT = "flux1-schnell-fp8.safetensors"
OUT_DIR = r"C:\Users\maxwi\ComfyUI-Shared\output"
PROJ_TEX = r"C:\Users\maxwi\Desktop\LeCoach3D\textures"
os.makedirs(PROJ_TEX, exist_ok=True)

# (output_name, seed, prompt)  — regenerating wall & roof as FLAT seamless swatches
TEXTURES = [
    ("wall_dark", 212,
     "flat seamless tileable texture swatch of dark charcoal near-black painted brick wall, "
     "industrial gym interior wall, straight-on orthographic elevation filling the entire "
     "frame edge to edge, no floor, no ceiling, no corner, no perspective, no vignette, "
     "uniform even flat lighting, high detail PBR material scan, 4k, no people, no text"),
    ("roof_steel", 213,
     "flat seamless tileable texture swatch of dark grey trapezoidal corrugated steel "
     "cladding sheet, industrial metal roof panel, straight-on orthographic view filling the "
     "whole frame, evenly spaced parallel ribs, subtle weathering, no perspective, no "
     "vignette, uniform even flat lighting, 4k material scan, no people, no text"),
]

def post(path, payload):
    req = urllib.request.Request(HOST+path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())
def get(path):
    with urllib.request.urlopen(HOST+path, timeout=30) as r: return json.loads(r.read())

def workflow(prefix, seed, pos):
    # FLUX schnell: 4 steps, cfg 1.0, euler/simple, SD3 latent, no negative guidance
    return {
        "4": {"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":CKPT}},
        "5": {"class_type":"EmptySD3LatentImage","inputs":{"width":1024,"height":1024,"batch_size":1}},
        "6": {"class_type":"CLIPTextEncode","inputs":{"text":pos,"clip":["4",1]}},
        "7": {"class_type":"CLIPTextEncode","inputs":{"text":"","clip":["4",1]}},
        "3": {"class_type":"KSampler","inputs":{
            "seed":seed,"steps":4,"cfg":1.0,"sampler_name":"euler","scheduler":"simple",
            "denoise":1.0,"model":["4",0],"positive":["6",0],"negative":["7",0],"latent_image":["5",0]}},
        "8": {"class_type":"VAEDecode","inputs":{"samples":["3",0],"vae":["4",2]}},
        "9": {"class_type":"SaveImage","inputs":{"filename_prefix":"lecoach_"+prefix,"images":["8",0]}},
    }

def generate(name, seed, pos):
    print(f"[{name}] queuing (FLUX schnell)...", flush=True)
    pid = post("/prompt", {"prompt": workflow(name, seed, pos)})["prompt_id"]
    for _ in range(300):            # up to 10 min (first run compiles/loads model)
        time.sleep(2)
        hist = get(f"/history/{pid}")
        if pid in hist:
            imgs = hist[pid].get("outputs",{}).get("9",{}).get("images",[])
            if imgs:
                src = os.path.join(OUT_DIR, imgs[0].get("subfolder",""), imgs[0]["filename"])
                dst = os.path.join(PROJ_TEX, name+".png")
                shutil.copyfile(src, dst); print(f"[{name}] DONE -> {dst}", flush=True); return True
    print(f"[{name}] TIMEOUT", flush=True); return False

if __name__ == "__main__":
    ok=0
    for n,s,p in TEXTURES:
        try:
            if generate(n,s,p): ok+=1
        except urllib.error.URLError as e:
            print(f"[{n}] ERROR {e}", flush=True)
    print(f"Completed {ok}/{len(TEXTURES)} FLUX textures.", flush=True)
