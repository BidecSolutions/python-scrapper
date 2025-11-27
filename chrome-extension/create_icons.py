"""Script to create placeholder icons for Chrome extension"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a simple icon with LeadFlux branding"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a gradient-like background (blue to purple)
    # For simplicity, we'll use a solid color with rounded corners effect
    # Main color: #4F46E5 (indigo)
    fill_color = (79, 70, 229, 255)  # #4F46E5
    
    # Draw rounded rectangle background
    margin = max(2, size // 8)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 4,
        fill=fill_color
    )
    
    # Add a simple "L" or "LF" text if size is large enough
    if size >= 48:
        try:
            # Try to use a font, fallback to default if not available
            font_size = size // 2
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            text = "LF" if size >= 64 else "L"
            # Calculate text position to center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((size - text_width) // 2, (size - text_height) // 2 - bbox[1])
            
            draw.text(position, text, fill=(255, 255, 255, 255), font=font)
        except Exception as e:
            print(f"Could not add text to {size}x{size} icon: {e}")
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"Created {output_path} ({size}x{size})")

def main():
    """Create all required icon sizes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, "icons")
    
    # Create icons directory if it doesn't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    sizes = [16, 48, 128]
    for size in sizes:
        output_path = os.path.join(icons_dir, f"icon{size}.png")
        create_icon(size, output_path)
    
    print("\nAll icons created successfully!")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Pillow (PIL) is required. Installing...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("Pillow installed. Running again...")
        main()

