#!/usr/bin/env python3
"""Generate seamless gym textures via the local ComfyUI API (SDXL base) and
copy them into the project's textures/ folder. Stdlib only."""
import json, time, urllib.request, urllib.error, shutil, os, sys

HOST = "http://127.0.0.1:8188"
CKPT = "sd_xl_base_1.0.safetensors"
OUT_DIR = r"C:\Users\maxwi\ComfyUI-Shared\output"
PROJ_TEX = r"C:\Users\maxwi\Desktop\LeCoach3D\textures"
os.makedirs(PROJ_TEX, exist_ok=True)

NEG = ("people, person, human, hands, text, letters, words, watermark, logo, "
       "signature, blurry, soft, low detail, distorted, jpeg artifacts, frame, border")

TEXTURES = [
    ("floor_rubber", 1,
     "seamless tileable texture of black rubber gym flooring, dense fine grey "
     "speckle fleck pattern, matte vulcanised rubber, top-down flat lay, orthographic, "
     "evenly diffuse lit, photorealistic, ultra detailed, 4k material scan"),
    ("wall_concrete", 2,
     "seamless tileable texture of dark charcoal grey painted breeze block concrete wall, "
     "industrial warehouse gym, subtle grunge and wear, matte, flat, orthographic, "
     "evenly lit, photorealistic, 4k material scan"),
    ("metal_steel", 3,
     "seamless tileable texture of brushed dark gunmetal steel, matte industrial metal "
     "surface, fine horizontal grain, subtle scratches, orthographic flat lay, evenly lit, "
     "photorealistic, 4k material scan"),
]

def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(HOST + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def get(path):
    with urllib.request.urlopen(HOST + path, timeout=30) as r:
        return json.loads(r.read())

def workflow(prefix, seed, pos):
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 28, "cfg": 7.0, "sampler_name": "dpmpp_2m",
            "scheduler": "karras", "denoise": 1.0,
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "lecoach_" + prefix, "images": ["8", 0]}},
    }

def generate(name, seed, pos):
    print(f"[{name}] queuing...", flush=True)
    res = post("/prompt", {"prompt": workflow(name, seed, pos)})
    pid = res["prompt_id"]
    # poll history
    for _ in range(180):  # up to 6 min
        time.sleep(2)
        hist = get(f"/history/{pid}")
        if pid in hist:
            outs = hist[pid].get("outputs", {})
            imgs = outs.get("9", {}).get("images", [])
            if imgs:
                fn = imgs[0]["filename"]; sub = imgs[0].get("subfolder", "")
                src = os.path.join(OUT_DIR, sub, fn)
                dst = os.path.join(PROJ_TEX, name + ".png")
                shutil.copyfile(src, dst)
                print(f"[{name}] DONE -> {dst}", flush=True)
                return True
    print(f"[{name}] TIMEOUT", flush=True)
    return False

if __name__ == "__main__":
    ok = 0
    for name, seed, pos in TEXTURES:
        try:
            if generate(name, seed, pos):
                ok += 1
        except urllib.error.URLError as e:
            print(f"[{name}] ERROR {e}", flush=True)
    print(f"Completed {ok}/{len(TEXTURES)} textures.", flush=True)
