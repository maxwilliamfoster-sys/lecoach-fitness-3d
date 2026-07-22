# Le Coach Fitness — 3D Walkthrough

A free, browser-based first-person 3D walkthrough of **Le Coach Fitness**, an independent gym at 2 Winship Road, Milton, Cambridge (CB24 6BQ).

**▶ Live demo:** https://maxwilliamfoster-sys.github.io/lecoach-fitness-3d/

## Controls
- **W A S D** / arrow keys — move
- **Mouse** — look around
- **Shift** — sprint
- **Esc** — release cursor

## What's inside
- `index.html` — the walkable app (Three.js, loaded from CDN; no build step). Open it directly or serve it statically.
- `textures/` — photoreal gym surfaces (rubber floor, breeze-block wall, brushed steel) generated locally with Stable Diffusion XL via ComfyUI.
- `lecoach_gym.blend` — the accurate building model (duo-pitch industrial unit, main hall, front-of-house, storage block), built to scale from the gym's build-vlog footage and OpenStreetMap footprint.
- `gen_textures.py` — regenerates the texture set from a local ComfyUI instance.

## Accuracy
The building shell (~32 m × 13 m, pitched steel-truss roof) is derived from the real OSM footprint and the Le Coach build-vlog series. Interior layout is an ongoing refinement.

## Tech
Three.js · PBR materials · image-based lighting · real-time planar mirror · bloom. 100% free/open tooling.

---
*This is a personal fan/reference project. Building footage referenced during development is not redistributed here.*
