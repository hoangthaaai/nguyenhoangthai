from PIL import Image, ImageDraw, ImageFont

def add_watermark(input_image_path, output_image_path, watermark_text):
    image = Image.open(input_image_path).convert("RGBA")

    watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    drawable = ImageDraw.Draw(watermark_layer)

    font_size = int(min(image.size) / 15)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # ✅ Cách mới tương thích Pillow >= 8.0.0
    bbox = drawable.textbbox((0, 0), watermark_text, font=font)
    textwidth = bbox[2] - bbox[0]
    textheight = bbox[3] - bbox[1]

    x = image.width - textwidth - 20
    y = image.height - textheight - 20

    drawable.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))

    watermarked = Image.alpha_composite(image, watermark_layer)
    watermarked.convert("RGB").save(output_image_path, "JPEG")
