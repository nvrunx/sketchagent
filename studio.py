#!/usr/bin/env python3
"""
SketchAgent Studio - Combined web interface with gallery, enhanced generation, and management
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import os
import json
import glob
import threading
import uuid
from datetime import datetime
from pathlib import Path
import base64
from PIL import Image
import io

# Import our enhanced utilities and original components
from enhanced_utils import COLOR_PALETTES, DRAWING_STYLES, get_palette_colors, choose_colors_for_concept
from enhanced_gen_sketch import EnhancedSketchApp
import utils

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app, resources={r"/*": {"origins": "*"}})

# In-memory storage for active generation tasks
active_tasks = {}
generation_queue = []

class SketchStudio:
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs("templates", exist_ok=True)
        os.makedirs("static/gallery", exist_ok=True)
    
    def scan_sketches(self):
        """Scan results directory for all generated sketches"""
        sketches = []
        
        if not os.path.exists(self.results_dir):
            return sketches
        
        for root, dirs, files in os.walk(self.results_dir):
            for file in files:
                if file.endswith('.png') and not file.startswith('init_canvas'):
                    sketch_path = os.path.join(root, file)
                    relative_path = os.path.relpath(sketch_path, self.results_dir)
                    
                    # Extract concept and style info from directory name
                    dir_name = os.path.basename(root)
                    concept = dir_name.split('_')[0] if '_' in dir_name else dir_name
                    
                    # Try to get style and palette info
                    style = 'unknown'
                    palette = 'unknown'
                    if '_' in dir_name:
                        parts = dir_name.split('_')
                        if len(parts) >= 3:
                            palette = parts[-2]
                            style = parts[-1]
                        elif len(parts) == 2:
                            style = parts[-1]
                    
                    # Get file info
                    stat = os.stat(sketch_path)
                    created_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Look for associated files
                    base_name = file.replace('.png', '')
                    svg_path = os.path.join(root, f"{base_name}.svg")
                    log_path = os.path.join(root, "experiment_log.json")
                    config_path = os.path.join(root, "generation_config.json")
                    
                    sketch_info = {
                        'id': relative_path.replace('/', '_').replace('.png', ''),
                        'concept': concept.replace('_', ' ').title(),
                        'style': style.title() if style != 'unknown' else 'Unknown',
                        'palette': palette.title() if palette != 'unknown' else 'Unknown',
                        'filename': file,
                        'path': sketch_path,
                        'relative_path': relative_path,
                        'created': created_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': created_time.timestamp(),
                        'has_svg': os.path.exists(svg_path),
                        'has_log': os.path.exists(log_path),
                        'has_config': os.path.exists(config_path),
                        'svg_path': svg_path if os.path.exists(svg_path) else None,
                        'log_path': log_path if os.path.exists(log_path) else None,
                        'config_path': config_path if os.path.exists(config_path) else None
                    }
                    
                    # Get image dimensions
                    try:
                        with Image.open(sketch_path) as img:
                            sketch_info['width'], sketch_info['height'] = img.size
                    except Exception:
                        sketch_info['width'], sketch_info['height'] = 0, 0
                    
                    # Load generation config if available
                    if sketch_info['has_config']:
                        try:
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                                sketch_info.update({
                                    'style': config.get('drawing_style', style).title(),
                                    'palette': config.get('color_palette', palette).title(),
                                    'colors_used': config.get('colors_used', {}),
                                    'enable_colors': config.get('enable_colors', True)
                                })
                        except Exception:
                            pass
                    
                    sketches.append(sketch_info)
        
        # Sort by creation time, newest first
        sketches.sort(key=lambda x: x['timestamp'], reverse=True)
        return sketches
    
    def get_sketch_details(self, sketch_id):
        """Get detailed information about a specific sketch"""
        sketches = self.scan_sketches()
        sketch = next((s for s in sketches if s['id'] == sketch_id), None)
        
        if not sketch:
            return None
        
        # Add conversation log if available
        if sketch['has_log']:
            try:
                with open(sketch['log_path'], 'r') as f:
                    sketch['conversation'] = json.load(f)
            except Exception:
                pass
        
        return sketch
    
    def delete_sketch(self, sketch_id):
        """Delete a sketch and its associated files"""
        sketch = self.get_sketch_details(sketch_id)
        if not sketch:
            return False
        
        try:
            files_to_delete = [sketch['path']]
            
            if sketch['has_svg'] and os.path.exists(sketch['svg_path']):
                files_to_delete.append(sketch['svg_path'])
            
            if sketch['has_log'] and os.path.exists(sketch['log_path']):
                files_to_delete.append(sketch['log_path'])
                
            if sketch['has_config'] and os.path.exists(sketch['config_path']):
                files_to_delete.append(sketch['config_path'])
            
            # Delete all files
            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Remove directory if empty
            sketch_dir = os.path.dirname(sketch['path'])
            if os.path.exists(sketch_dir) and not os.listdir(sketch_dir):
                os.rmdir(sketch_dir)
            
            return True
        except Exception as e:
            print(f"Error deleting sketch {sketch_id}: {e}")
            return False

def generate_sketch_async(task_id, args_dict):
    """Generate sketch in background thread"""
    try:
        active_tasks[task_id]['status'] = 'generating'
        active_tasks[task_id]['progress'] = 10
        
        # Create args object
        class Args:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        args = Args(**args_dict)
        
        active_tasks[task_id]['progress'] = 20
        
        # Initialize sketch app
        sketch_app = EnhancedSketchApp(args)
        active_tasks[task_id]['progress'] = 30
        
        # Generate sketches
        results = sketch_app.generate_sketches()
        
        active_tasks[task_id]['status'] = 'completed'
        active_tasks[task_id]['progress'] = 100
        active_tasks[task_id]['results'] = results
        active_tasks[task_id]['path'] = args.path2save
        
    except Exception as e:
        active_tasks[task_id]['status'] = 'error'
        active_tasks[task_id]['error'] = str(e)
        active_tasks[task_id]['progress'] = 0

# Initialize studio
studio = SketchStudio()

# Routes
@app.route('/')
def home():
    """Main studio interface"""
    return render_template('studio.html')

@app.route('/gallery')
def gallery():
    """Gallery page"""
    return render_template('gallery.html')

@app.route('/generate')
def generate_page():
    """Generation page"""
    return render_template('generate.html')

# API Routes
@app.route('/api/sketches')
def api_sketches():
    """Get all sketches"""
    sketches = studio.scan_sketches()
    
    for sketch in sketches:
        sketch['url'] = f"/sketch-image/{sketch['id']}"
        if sketch['has_svg']:
            sketch['svg_url'] = f"/sketch-svg/{sketch['id']}"
    
    return jsonify(sketches)

@app.route('/api/sketch/<sketch_id>')
def api_sketch_details(sketch_id):
    """Get sketch details"""
    sketch = studio.get_sketch_details(sketch_id)
    if not sketch:
        return jsonify({'error': 'Sketch not found'}), 404
    
    sketch['url'] = f"/sketch-image/{sketch['id']}"
    if sketch['has_svg']:
        sketch['svg_url'] = f"/sketch-svg/{sketch['id']}"
    
    return jsonify(sketch)

@app.route('/api/sketch/<sketch_id>/delete', methods=['POST'])
def api_delete_sketch(sketch_id):
    """Delete a sketch"""
    success = studio.delete_sketch(sketch_id)
    return jsonify({'success': success})

@app.route('/api/palettes')
def api_palettes():
    """Get available color palettes"""
    return jsonify({
        name: {**palette, 'name': name.title()} 
        for name, palette in COLOR_PALETTES.items()
    })

@app.route('/api/styles')
def api_styles():
    """Get available drawing styles"""
    return jsonify({
        name: {**style, 'id': name} 
        for name, style in DRAWING_STYLES.items()
    })

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Start sketch generation"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('concept_to_draw'):
        return jsonify({'error': 'Concept is required'}), 400
    
    # Create task ID
    task_id = str(uuid.uuid4())
    
    # Prepare arguments
    args_dict = {
        'concept_to_draw': data['concept_to_draw'],
        'color_palette': data.get('color_palette', 'vibrant'),
        'drawing_style': data.get('drawing_style', 'sketch'),
        'enable_colors': data.get('enable_colors', True),
        'num_variations': data.get('num_variations', 1),
        'seed_mode': data.get('seed_mode', 'stochastic'),
        'model': data.get('model', 'gemini-1.5-flash'),
        'gen_mode': 'generation',
        'res': 50,
        'cell_size': 12,
        'stroke_width': 7.0,
        'path2save': f"results/enhanced/{data['concept_to_draw'].replace(' ', '_')}_{data.get('color_palette', 'vibrant')}_{data.get('drawing_style', 'sketch')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    # Calculate grid size
    args_dict['grid_size'] = (args_dict['res'] + 1) * args_dict['cell_size']
    args_dict['save_name'] = args_dict['concept_to_draw'].replace(" ", "_")
    
    # Create task record
    active_tasks[task_id] = {
        'id': task_id,
        'status': 'queued',
        'progress': 0,
        'concept': data['concept_to_draw'],
        'style': data.get('drawing_style', 'sketch'),
        'palette': data.get('color_palette', 'vibrant'),
        'variations': data.get('num_variations', 1),
        'created': datetime.now().isoformat()
    }
    
    # Start generation in background
    thread = threading.Thread(target=generate_sketch_async, args=(task_id, args_dict))
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/api/task/<task_id>')
def api_task_status(task_id):
    """Get task status"""
    task = active_tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(task)

@app.route('/api/stats')
def api_stats():
    """Get gallery statistics"""
    sketches = studio.scan_sketches()
    
    total = len(sketches)
    concepts = len(set(s['concept'] for s in sketches))
    styles = len(set(s['style'] for s in sketches))
    palettes = len(set(s['palette'] for s in sketches))
    
    today = datetime.now().date()
    today_count = len([s for s in sketches if datetime.fromtimestamp(s['timestamp']).date() == today])
    
    return jsonify({
        'total_sketches': total,
        'unique_concepts': concepts,
        'unique_styles': styles,
        'unique_palettes': palettes,
        'today_sketches': today_count
    })

# File serving routes
@app.route('/sketch-image/<sketch_id>')
def serve_sketch_image(sketch_id):
    """Serve sketch images"""
    sketch = studio.get_sketch_details(sketch_id)
    if not sketch or not os.path.exists(sketch['path']):
        return "Image not found", 404
    return send_from_directory(os.path.dirname(sketch['path']), os.path.basename(sketch['path']))

@app.route('/sketch-svg/<sketch_id>')
def serve_sketch_svg(sketch_id):
    """Serve sketch SVG files"""
    sketch = studio.get_sketch_details(sketch_id)
    if not sketch or not sketch['has_svg'] or not os.path.exists(sketch['svg_path']):
        return "SVG not found", 404
    return send_from_directory(os.path.dirname(sketch['svg_path']), os.path.basename(sketch['svg_path']))

if __name__ == '__main__':
    print("🎨 SketchAgent Studio")
    print("=" * 40)
    print("🖼️ Gallery: View and manage sketches")
    print("✨ Enhanced Generation: Colors and styles")  
    print("🎯 All-in-one interface")
    print("=" * 40)
    print("Server starting at: http://localhost:5002")
    print("=" * 40)
    
    studio.ensure_directories()
    
    app.run(debug=True, port=5002, host='0.0.0.0')