# ply2mesh_geo_tex_main.py
#
# Usage example (in Colab, from the DreamGaussian repo root):
#   python ply2mesh_geo_tex_main.py \
#       --config configs/text.yaml \
#       --ply /content/path/to/your_3dgs.ply \
#       save_path=icecream outdir=/content/output
#
# This will:
#   - load the given 3DGS .ply (DreamGaussian format)
#   - run GUI.save_model(mode="geo+tex") from main.py
#   - save mesh + texture in the same way as main.py (geo+tex mode)

import os
import argparse

from omegaconf import OmegaConf

# Import GUI and everything else from the original main.py
from main import GUI


def main():
    parser = argparse.ArgumentParser(
        description="Convert a DreamGaussian-style 3DGS .ply to mesh+texture using the same geo+tex pipeline as main.py."
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the YAML config file used by DreamGaussian (same as main.py).",
    )
    parser.add_argument(
        "--ply",
        type=str,
        required=True,
        help="Path to the input DreamGaussian-format 3DGS .ply file.",
    )
    parser.add_argument(
        "--texture_size",
        type=int,
        default=1024,
        help="Texture resolution (H=W) to use for geo+tex baking. Default: 1024.",
    )

    # We use parse_known_args to forward extra options (like save_path=..., outdir=...)
    # directly to OmegaConf as CLI overrides, exactly like main.py.
    args, extras = parser.parse_known_args()

    # Load base config
    opt = OmegaConf.load(args.config)

    # Apply CLI overrides (e.g., save_path=..., outdir=..., mesh_format=...)
    if extras:
        opt = OmegaConf.merge(opt, OmegaConf.from_cli(extras))

    # Make sure GUI is disabled (we only need the renderer, not the DearPyGui window)
    opt.gui = False

    # Create the same GUI object as in main.py (this sets up Renderer, Gaussians, etc.)
    gui = GUI(opt)

    # Overwrite the random-initialized Gaussians with your pre-trained 3DGS .ply
    print(f"[INFO] Loading 3DGS from: {args.ply}")
    gui.renderer.gaussians.load_ply(args.ply)

    # Run the exact same geo+tex save pipeline as in main.py
    print("[INFO] Saving mesh + texture using geo+tex mode...")
    gui.save_model(mode="geo+tex", texture_size=args.texture_size)
    print("[INFO] Done.")


if __name__ == "__main__":
    main()
