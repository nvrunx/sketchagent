#!/usr/bin/env python3
"""
SVG to PNG converter that replaces cairosvg functionality.
This module provides an alternative to cairosvg>=2.7.1 for converting SVG files to PNG.
"""

import os
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import re
from typing import Tuple, Optional, List


def parse_svg_dimensions(svg_content: str) -> Tuple[int, int]:
    """
    Extract width and height from SVG content.
    Returns (width, height) in pixels.
    """
    try:
        root = ET.fromstring(svg_content)
        width = root.get('width', '100')
        height = root.get('height', '100')
        
        # Remove units and convert to int
        width = int(re.sub(r'[^\d.]', '', str(width)))
        height = int(re.sub(r'[^\d.]', '', str(height)))
        
        return width, height
    except:
        return 100, 100  # Default size


def parse_stroke_color(stroke_str: str) -> str:
    """Parse stroke color, default to black if not specified."""
    if not stroke_str or stroke_str == 'none':
        return 'black'
    return stroke_str


def parse_stroke_width(stroke_width_str: str) -> float:
    """Parse stroke width, default to 1.0 if not specified."""
    if not stroke_width_str:
        return 1.0
    try:
        return float(re.sub(r'[^\d.]', '', str(stroke_width_str)))
    except:
        return 1.0


def parse_path_data(path_d: str) -> List[Tuple[str, List[float]]]:
    """
    Parse SVG path data into command-coordinate pairs.
    Returns list of (command, coordinates) tuples.
    """
    commands = []
    
    # Split path data into tokens
    tokens = re.findall(r'[MLCQZmlcqz]|[-+]?[0-9]*\.?[0-9]+', path_d)
    
    i = 0
    current_command = 'M'
    
    while i < len(tokens):
        token = tokens[i]
        
        # Check if token is a command
        if token in 'MLCQZmlcqz':
            current_command = token
            i += 1
            continue
        
        # Parse coordinates for current command
        coords = []
        
        if current_command in 'Mm':  # Move to
            coords = [float(tokens[i]), float(tokens[i+1])]
            i += 2
        elif current_command in 'Ll':  # Line to
            coords = [float(tokens[i]), float(tokens[i+1])]
            i += 2
        elif current_command in 'Cc':  # Cubic Bezier
            coords = [float(tokens[i+j]) for j in range(6)]
            i += 6
        elif current_command in 'Qq':  # Quadratic Bezier
            coords = [float(tokens[i+j]) for j in range(4)]
            i += 4
        elif current_command in 'Zz':  # Close path
            coords = []
        else:
            i += 1
            continue
        
        commands.append((current_command, coords))
        
        # After first M, implicit commands become L
        if current_command == 'M':
            current_command = 'L'
        elif current_command == 'm':
            current_command = 'l'
    
    return commands


def draw_path_on_image(draw: ImageDraw.ImageDraw, path_commands: List[Tuple[str, List[float]]], 
                      stroke_color: str, stroke_width: float):
    """Draw a path on PIL Image using path commands."""
    
    current_point = [0, 0]
    path_start = [0, 0]
    
    # Convert path commands to drawable segments
    points = []
    
    for command, coords in path_commands:
        if command == 'M':  # Move to (absolute)
            current_point = [coords[0], coords[1]]
            path_start = current_point.copy()
            points = [current_point.copy()]
        elif command == 'm':  # Move to (relative)
            current_point[0] += coords[0]
            current_point[1] += coords[1]
            path_start = current_point.copy()
            points = [current_point.copy()]
        elif command == 'L':  # Line to (absolute)
            new_point = [coords[0], coords[1]]
            points.append(new_point)
            current_point = new_point
        elif command == 'l':  # Line to (relative)
            new_point = [current_point[0] + coords[0], current_point[1] + coords[1]]
            points.append(new_point)
            current_point = new_point
        elif command in 'Cc':  # Cubic Bezier (simplified to line segments)
            # For simplicity, we'll approximate Bezier curves with line segments
            if command == 'C':  # Absolute
                end_point = [coords[4], coords[5]]
            else:  # Relative
                end_point = [current_point[0] + coords[4], current_point[1] + coords[5]]
            
            # Create intermediate points for smooth curve approximation
            num_segments = 10
            for i in range(1, num_segments + 1):
                t = i / num_segments
                # Simple linear interpolation (could be improved with actual Bezier math)
                interp_point = [
                    current_point[0] + t * (end_point[0] - current_point[0]),
                    current_point[1] + t * (end_point[1] - current_point[1])
                ]
                points.append(interp_point)
            
            current_point = end_point
        elif command in 'Qq':  # Quadratic Bezier (simplified)
            if command == 'Q':  # Absolute
                end_point = [coords[2], coords[3]]
            else:  # Relative
                end_point = [current_point[0] + coords[2], current_point[1] + coords[3]]
            
            # Approximate with line segments
            num_segments = 8
            for i in range(1, num_segments + 1):
                t = i / num_segments
                interp_point = [
                    current_point[0] + t * (end_point[0] - current_point[0]),
                    current_point[1] + t * (end_point[1] - current_point[1])
                ]
                points.append(interp_point)
            
            current_point = end_point
        elif command in 'Zz':  # Close path
            if len(points) > 0:
                points.append(path_start.copy())
    
    # Draw the path as connected lines
    if len(points) > 1:
        # Convert to tuple format for PIL
        pil_points = [(int(p[0]), int(p[1])) for p in points]
        
        # Draw lines connecting the points
        for i in range(len(pil_points) - 1):
            draw.line([pil_points[i], pil_points[i+1]], 
                     fill=stroke_color, width=int(stroke_width))


def svg_to_png(svg_input: str, output_path: str, background_color: str = "white") -> bool:
    """
    Convert SVG to PNG using PIL.
    
    Args:
        svg_input: Either SVG content string or path to SVG file
        output_path: Path where PNG will be saved
        background_color: Background color for the PNG
    
    Returns:
        True if conversion successful, False otherwise
    """
    try:
        # Read SVG content
        if os.path.exists(svg_input):
            with open(svg_input, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        else:
            svg_content = svg_input
        
        # Parse SVG dimensions
        width, height = parse_svg_dimensions(svg_content)
        
        # Create PIL image
        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Parse SVG XML
        root = ET.fromstring(svg_content)
        
        # Build parent map for attribute inheritance
        parent_map = {}
        for parent in root.iter():
            for child in parent:
                parent_map[child] = parent
        
        # Process each group and path element
        for elem in root.iter():
            if elem.tag.endswith('path'):
                # Get path attributes
                path_d = elem.get('d', '')
                stroke = elem.get('stroke')
                stroke_width = elem.get('stroke-width')
                
                # Get attributes from parent group if not directly specified
                parent = parent_map.get(elem)
                if parent is not None:
                    if not stroke or stroke == 'none':
                        stroke = parent.get('stroke', 'black')
                    if not stroke_width:
                        stroke_width = parent.get('stroke-width', '1')
                
                # Set defaults if still not found
                if not stroke or stroke == 'none':
                    stroke = 'black'
                if not stroke_width:
                    stroke_width = '1'
                
                # Parse and draw the path
                if path_d:
                    stroke_color = parse_stroke_color(stroke)
                    width = parse_stroke_width(stroke_width)
                    path_commands = parse_path_data(path_d)
                    draw_path_on_image(draw, path_commands, stroke_color, width)
        
        # Save the image
        img.save(output_path, 'PNG')
        return True
        
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        return False


def svg2png(url: str = None, file_obj=None, write_to: str = None, 
           background_color: str = "white", **kwargs) -> bool:
    """
    Compatibility function that mimics cairosvg.svg2png interface.
    
    Args:
        url: Path to SVG file (compatible with cairosvg's 'url' parameter)
        file_obj: Not implemented (for compatibility)
        write_to: Output PNG file path
        background_color: Background color
        **kwargs: Additional parameters (ignored for compatibility)
    
    Returns:
        True if successful, False otherwise
    """
    if not url or not write_to:
        raise ValueError("Both 'url' and 'write_to' parameters are required")
    
    return svg_to_png(url, write_to, background_color)


# Test function
if __name__ == "__main__":
    # Create a test SVG
    test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <g stroke="black" stroke-width="3" fill="none" stroke-linecap="round">
        <path d="M 50 50 L 150 50 L 150 150 L 50 150 Z"/>
        <path d="M 100 75 Q 125 100 100 125 Q 75 100 100 75"/>
    </g>
</svg>'''
    
    # Test the conversion
    result = svg_to_png(test_svg, '/tmp/test_conversion.png')
    if result:
        print("✅ SVG to PNG conversion test successful!")
        if os.path.exists('/tmp/test_conversion.png'):
            size = os.path.getsize('/tmp/test_conversion.png')
            print(f"Generated PNG size: {size} bytes")
        else:
            print("❌ PNG file not found")
    else:
        print("❌ SVG to PNG conversion test failed")