#!/usr/bin/env python3
"""
Create sample sketches for testing the gallery
"""

from PIL import Image, ImageDraw
import os
import json
from datetime import datetime

def create_sample_sketch(concept, filename, size=(612, 612)):
    """Create a simple sample sketch"""
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw different shapes based on concept
    if concept == "cat":
        # Simple cat face
        # Head circle
        draw.ellipse([200, 200, 400, 400], outline='black', width=3)
        # Ears
        draw.polygon([(180, 220), (220, 160), (240, 200)], outline='black', width=3)
        draw.polygon([(372, 200), (392, 160), (432, 220)], outline='black', width=3)
        # Eyes
        draw.ellipse([230, 250, 260, 280], outline='black', width=2)
        draw.ellipse([352, 250, 382, 280], outline='black', width=2)
        # Nose
        draw.polygon([(300, 300), (290, 320), (310, 320)], outline='black', width=2)
        # Mouth
        draw.arc([280, 320, 332, 360], 0, 180, fill='black', width=2)
    elif concept == "house":
        # Simple house
        # Base rectangle
        draw.rectangle([200, 300, 400, 500], outline='black', width=3)
        # Roof triangle
        draw.polygon([(180, 300), (300, 200), (420, 300)], outline='black', width=3)
        # Door
        draw.rectangle([280, 400, 320, 500], outline='black', width=2)
        # Window
        draw.rectangle([340, 350, 380, 390], outline='black', width=2)
    elif concept == "tree":
        # Simple tree
        # Trunk
        draw.rectangle([290, 400, 320, 500], outline='black', width=3, fill='brown')
        # Crown
        draw.ellipse([220, 200, 380, 400], outline='black', width=3, fill='green')
    
    return img

def create_sample_svg(concept):
    """Create a simple SVG for the concept"""
    if concept == "cat":
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="612" height="612" xmlns="http://www.w3.org/2000/svg">
  <circle cx="300" cy="300" r="100" fill="none" stroke="black" stroke-width="3"/>
  <polygon points="180,220 220,160 240,200" fill="none" stroke="black" stroke-width="3"/>
  <polygon points="372,200 392,160 432,220" fill="none" stroke="black" stroke-width="3"/>
  <circle cx="245" cy="265" r="15" fill="none" stroke="black" stroke-width="2"/>
  <circle cx="367" cy="265" r="15" fill="none" stroke="black" stroke-width="2"/>
</svg>'''
    elif concept == "house":
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="612" height="612" xmlns="http://www.w3.org/2000/svg">
  <rect x="200" y="300" width="200" height="200" fill="none" stroke="black" stroke-width="3"/>
  <polygon points="180,300 300,200 420,300" fill="none" stroke="black" stroke-width="3"/>
  <rect x="280" y="400" width="40" height="100" fill="none" stroke="black" stroke-width="2"/>
  <rect x="340" y="350" width="40" height="40" fill="none" stroke="black" stroke-width="2"/>
</svg>'''
    else:
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="612" height="612" xmlns="http://www.w3.org/2000/svg">
  <circle cx="300" cy="300" r="50" fill="none" stroke="black" stroke-width="3"/>
</svg>'''

def create_sample_log(concept):
    """Create a sample experiment log"""
    return [
        {
            "role": "system",
            "content": f"You are an expert artist specializing in drawing sketches. Create a {concept}."
        },
        {
            "role": "user", 
            "content": f"Please draw a {concept} using the grid coordinate system."
        },
        {
            "role": "assistant",
            "content": f"<answer><concept>{concept}</concept><strokes><s1><points>x25y25, x30y30, x35y25</points><t_values>0.0, 0.5, 1.0</t_values><id>{concept} sketch</id></s1></strokes></answer>"
        }
    ]

def create_samples():
    """Create sample sketches for testing"""
    concepts = ["cat", "house", "tree", "flower", "car"]
    
    for i, concept in enumerate(concepts):
        # Create directory
        sketch_dir = f"results/test/{concept}"
        os.makedirs(sketch_dir, exist_ok=True)
        
        # Create PNG
        img = create_sample_sketch(concept, f"{concept}.png")
        png_path = f"{sketch_dir}/{concept}.png"
        img.save(png_path)
        
        # Create canvas version
        canvas_img = Image.new('RGB', (612, 612), 'white')
        # Add grid (simplified)
        canvas_img.paste(img, (0, 0))
        canvas_path = f"{sketch_dir}/{concept}_canvas.png"
        canvas_img.save(canvas_path)
        
        # Create SVG
        svg_content = create_sample_svg(concept)
        svg_path = f"{sketch_dir}/{concept}.svg"
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        # Create log
        log_content = create_sample_log(concept)
        log_path = f"{sketch_dir}/experiment_log.json"
        with open(log_path, 'w') as f:
            json.dump(log_content, f, indent=4)
        
        print(f"✅ Created sample sketch: {concept}")

if __name__ == "__main__":
    print("🎨 Creating sample sketches for gallery testing...")
    create_samples()
    print("✅ All sample sketches created!")
    print("📁 Files created in results/test/ directory")