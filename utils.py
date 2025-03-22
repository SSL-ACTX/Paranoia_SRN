from PIL import Image, ImageDraw

def create_circular_image(image_path, size):
    """Circular image for profile?"""
    try:
        image = Image.open(image_path).resize(size)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        circular_image = Image.new("RGBA", size)
        circular_image.paste(image, (0, 0), mask=mask)
        return circular_image
    except FileNotFoundError:
        print(f"Image not found: {image_path}")
        return None
