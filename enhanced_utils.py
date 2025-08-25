"""
Enhanced sketching utilities with color support and multiple styles
"""

import colorsys
import random
from typing import List, Tuple, Dict, Optional

# Color palettes for different styles
COLOR_PALETTES = {
    'monochrome': {
        'primary': '#000000',
        'secondary': '#666666', 
        'accent': '#333333',
        'background': '#ffffff'
    },
    'vibrant': {
        'primary': '#FF6B6B',
        'secondary': '#4ECDC4',
        'accent': '#45B7D1',
        'highlight': '#96CEB4',
        'background': '#FFEAA7'
    },
    'nature': {
        'primary': '#2E7D32',
        'secondary': '#8BC34A', 
        'accent': '#4CAF50',
        'earth': '#8D6E63',
        'sky': '#03DAC6',
        'background': '#F1F8E9'
    },
    'sunset': {
        'primary': '#FF6F00',
        'secondary': '#FF8F00',
        'accent': '#FFA000',
        'warm': '#FFB74D',
        'glow': '#FFCC02',
        'background': '#FFF8E1'
    },
    'ocean': {
        'primary': '#0277BD',
        'secondary': '#0288D1',
        'accent': '#029BE5',
        'deep': '#01579B',
        'foam': '#B3E5FC',
        'background': '#E1F5FE'
    },
    'pastel': {
        'primary': '#F8BBD9',
        'secondary': '#E4C1F9',
        'accent': '#A8DADC',
        'soft': '#F1FAEE',
        'gentle': '#FFD6E6',
        'background': '#FFFFFF'
    }
}

# Drawing styles with their characteristics
DRAWING_STYLES = {
    'sketch': {
        'name': 'Sketch Style',
        'stroke_width_range': (1.0, 3.0),
        'line_variation': True,
        'rough_edges': True,
        'opacity_range': (0.7, 1.0),
        'description': 'Hand-drawn sketch with natural line variations'
    },
    'cartoon': {
        'name': 'Cartoon Style', 
        'stroke_width_range': (2.0, 5.0),
        'line_variation': False,
        'rough_edges': False,
        'opacity_range': (1.0, 1.0),
        'description': 'Bold, clean cartoon-style lines'
    },
    'watercolor': {
        'name': 'Watercolor Style',
        'stroke_width_range': (3.0, 8.0),
        'line_variation': True,
        'rough_edges': True,
        'opacity_range': (0.3, 0.8),
        'description': 'Soft, flowing watercolor effect'
    },
    'minimalist': {
        'name': 'Minimalist Style',
        'stroke_width_range': (1.0, 2.0),
        'line_variation': False,
        'rough_edges': False,
        'opacity_range': (0.9, 1.0),
        'description': 'Clean, simple lines with minimal detail'
    },
    'artistic': {
        'name': 'Artistic Style',
        'stroke_width_range': (2.0, 6.0),
        'line_variation': True,
        'rough_edges': True,
        'opacity_range': (0.6, 1.0),
        'description': 'Expressive artistic style with varied strokes'
    }
}

def get_palette_colors(palette_name: str) -> Dict[str, str]:
    """Get colors from a named palette"""
    return COLOR_PALETTES.get(palette_name, COLOR_PALETTES['monochrome'])

def get_style_config(style_name: str) -> Dict:
    """Get configuration for a drawing style"""
    return DRAWING_STYLES.get(style_name, DRAWING_STYLES['sketch'])

def generate_color_variations(base_color: str, count: int = 5) -> List[str]:
    """Generate color variations from a base color"""
    # Convert hex to HSV
    base_color = base_color.lstrip('#')
    r, g, b = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    
    variations = []
    for i in range(count):
        # Vary hue, saturation, and value slightly
        new_h = (h + random.uniform(-0.1, 0.1)) % 1.0
        new_s = max(0.1, min(1.0, s + random.uniform(-0.2, 0.2)))
        new_v = max(0.3, min(1.0, v + random.uniform(-0.2, 0.2)))
        
        # Convert back to RGB
        rgb = colorsys.hsv_to_rgb(new_h, new_s, new_v)
        hex_color = '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        variations.append(hex_color)
    
    return variations

def choose_colors_for_concept(concept: str, palette: str = 'vibrant') -> Dict[str, str]:
    """Choose appropriate colors for a concept"""
    palette_colors = get_palette_colors(palette)
    
    # Concept-specific color logic
    concept_lower = concept.lower()
    
    if 'cat' in concept_lower or 'dog' in concept_lower or 'animal' in concept_lower:
        if palette == 'nature':
            return {
                'outline': palette_colors['primary'],
                'fill': palette_colors['earth'],
                'accent': palette_colors['accent']
            }
    elif 'house' in concept_lower or 'building' in concept_lower:
        if palette == 'nature':
            return {
                'outline': palette_colors['earth'],
                'fill': palette_colors['secondary'],
                'accent': palette_colors['primary']
            }
    elif 'flower' in concept_lower or 'tree' in concept_lower or 'plant' in concept_lower:
        return {
            'outline': palette_colors['primary'],
            'fill': palette_colors['secondary'],
            'accent': palette_colors['accent']
        }
    elif 'car' in concept_lower or 'vehicle' in concept_lower:
        if palette == 'vibrant':
            return {
                'outline': palette_colors['primary'],
                'fill': palette_colors['accent'],
                'accent': palette_colors['secondary']
            }
    elif 'sun' in concept_lower or 'star' in concept_lower:
        if palette in ['sunset', 'vibrant']:
            return {
                'outline': palette_colors['primary'],
                'fill': palette_colors['secondary'],
                'accent': palette_colors.get('glow', palette_colors['accent'])
            }
    elif 'water' in concept_lower or 'ocean' in concept_lower or 'sea' in concept_lower:
        if palette == 'ocean':
            return {
                'outline': palette_colors['deep'],
                'fill': palette_colors['secondary'],
                'accent': palette_colors['foam']
            }
    
    # Default color assignment
    return {
        'outline': palette_colors['primary'],
        'fill': palette_colors.get('secondary', palette_colors['primary']),
        'accent': palette_colors.get('accent', palette_colors['primary'])
    }

def format_colored_svg(control_points, dim=(612, 612), colors=None, style='sketch'):
    """Generate SVG with color and style support"""
    if colors is None:
        colors = {'outline': '#000000', 'fill': 'none', 'accent': '#666666'}
    
    style_config = get_style_config(style)
    
    width, height = dim
    
    # Start SVG
    svg_content = [f'<?xml version="1.0" encoding="UTF-8"?>']
    svg_content.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">')
    
    # Add style definitions if needed
    if style == 'watercolor':
        svg_content.append('''
        <defs>
            <filter id="roughPaper" x="0%" y="0%" width="100%" height="100%">
                <feTurbulence baseFrequency="0.04" numOctaves="5" result="noise"/>
                <feDisplacementMap in="SourceGraphic" in2="noise" scale="1"/>
            </filter>
        </defs>
        ''')
    
    stroke_width_min, stroke_width_max = style_config['stroke_width_range']
    opacity_min, opacity_max = style_config['opacity_range']
    
    # Draw each stroke
    color_index = 0
    color_keys = list(colors.keys())
    
    for i, stroke_points in enumerate(control_points):
        if len(stroke_points) < 2:
            continue
            
        # Choose color for this stroke
        color_key = color_keys[color_index % len(color_keys)]
        stroke_color = colors[color_key]
        color_index += 1
        
        # Vary stroke properties based on style
        if style_config['line_variation']:
            stroke_width = random.uniform(stroke_width_min, stroke_width_max)
            opacity = random.uniform(opacity_min, opacity_max)
        else:
            stroke_width = (stroke_width_min + stroke_width_max) / 2
            opacity = opacity_max
        
        # Build path
        if len(stroke_points) == 1:
            # Single point (dot)
            x, y = stroke_points[0]
            svg_content.append(f'  <circle cx="{x}" cy="{y}" r="{stroke_width/2}" fill="{stroke_color}" opacity="{opacity}"/>')
        elif len(stroke_points) == 2:
            # Straight line
            x1, y1 = stroke_points[0]
            x2, y2 = stroke_points[1]
            extra_attrs = ''
            if style == 'watercolor':
                extra_attrs = 'filter="url(#roughPaper)"'
            svg_content.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity}" {extra_attrs}/>')
        else:
            # Bezier curve
            path_data = f"M {stroke_points[0][0]} {stroke_points[0][1]}"
            
            # Create smooth curve through points
            for j in range(1, len(stroke_points)):
                if j == len(stroke_points) - 1:
                    # Last point
                    path_data += f" L {stroke_points[j][0]} {stroke_points[j][1]}"
                else:
                    # Use quadratic bezier curves
                    if j + 1 < len(stroke_points):
                        cx, cy = stroke_points[j]
                        ex, ey = stroke_points[j + 1]
                        path_data += f" Q {cx} {cy} {ex} {ey}"
                        j += 1  # Skip next point as it's used as end point
                    else:
                        path_data += f" L {stroke_points[j][0]} {stroke_points[j][1]}"
            
            extra_attrs = ''
            if style == 'watercolor':
                extra_attrs = 'filter="url(#roughPaper)"'
            
            svg_content.append(f'  <path d="{path_data}" fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity}" {extra_attrs}/>')
    
    svg_content.append('</svg>')
    return '\n'.join(svg_content)

def enhance_sketch_prompt(base_prompt: str, palette: str = 'vibrant', style: str = 'sketch') -> str:
    """Enhance the sketch prompt with color and style instructions"""
    palette_info = get_palette_colors(palette)
    style_info = get_style_config(style)
    
    color_instruction = f"\nUse colors from the {palette} palette: {', '.join(palette_info.values())}."
    style_instruction = f"\nDraw in {style_info['name'].lower()} with {style_info['description'].lower()}."
    
    enhanced_prompt = base_prompt + color_instruction + style_instruction
    enhanced_prompt += f"\nConsider varying stroke weights between {style_info['stroke_width_range'][0]} and {style_info['stroke_width_range'][1]} for visual interest."
    
    return enhanced_prompt

# Export the main functions
__all__ = [
    'COLOR_PALETTES', 'DRAWING_STYLES', 'get_palette_colors', 'get_style_config',
    'generate_color_variations', 'choose_colors_for_concept', 'format_colored_svg',
    'enhance_sketch_prompt'
]