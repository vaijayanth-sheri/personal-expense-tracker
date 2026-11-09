"""
Generates the custom Modern Geometric Euro Vault icon (.ico and .png).
"""

import os
from PIL import Image, ImageDraw, ImageFont

def generate_vault_icon():
    os.makedirs("assets", exist_ok=True)
    os.makedirs("web", exist_ok=True)

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background Rounded Shield / Hexagonal Vault
    # Draw outer glow / border
    pad = 16
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=48,
        fill="#0f172a",
        outline="#38bdf8",
        width=8
    )

    # Inner soft vault plate
    inner_pad = 32
    draw.rounded_rectangle(
        [inner_pad, inner_pad, size - inner_pad, size - inner_pad],
        radius=36,
        fill="#1e293b",
        outline="#0284c7",
        width=3
    )

    # Decorative tech corner accents
    corner_size = 14
    accent_color = "#38bdf8"
    draw.rectangle([inner_pad + 10, inner_pad + 10, inner_pad + 10 + corner_size, inner_pad + 14], fill=accent_color)
    draw.rectangle([size - inner_pad - 10 - corner_size, inner_pad + 10, size - inner_pad - 10, inner_pad + 14], fill=accent_color)
    draw.rectangle([inner_pad + 10, size - inner_pad - 14, inner_pad + 10 + corner_size, size - inner_pad - 10], fill=accent_color)
    draw.rectangle([size - inner_pad - 10 - corner_size, size - inner_pad - 14, size - inner_pad - 10, size - inner_pad - 10], fill=accent_color)

    # Draw Geometric Euro Sign (€) in center
    cx, cy = size // 2, size // 2
    r_outer = 64
    r_inner = 42

    # Draw outer arc of Euro 'C'
    draw.arc([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], start=40, end=320, fill="#38bdf8", width=18)

    # Draw crossbars for €
    draw.line([cx - 48, cy - 14, cx + 24, cy - 14], fill="#f8fafc", width=10)
    draw.line([cx - 48, cy + 14, cx + 24, cy + 14], fill="#f8fafc", width=10)

    # Save PNG
    png_path = os.path.join("assets", "icon.png")
    img.save(png_path, "PNG")
    img.save(os.path.join("web", "icon.png"), "PNG")

    # Save multi-size ICO
    ico_path = os.path.join("assets", "icon.ico")
    img.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    )
    img.save(
        os.path.join("web", "favicon.ico"),
        format="ICO",
        sizes=[(48, 48), (32, 32), (16, 16)]
    )
    print("Generated icon.ico and icon.png successfully!")

if __name__ == "__main__":
    generate_vault_icon()
