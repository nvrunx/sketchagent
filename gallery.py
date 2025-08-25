#!/usr/bin/env python3
"""
SketchAgent Gallery - View and manage generated sketches
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import glob
from datetime import datetime
from pathlib import Path
import base64
from PIL import Image
import io

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app, resources={r"/*": {"origins": "*"}})

class SketchGallery:
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
        
        # Look for sketch directories and files
        for root, dirs, files in os.walk(self.results_dir):
            for file in files:
                if file.endswith('.png') and not file.startswith('init_canvas'):
                    sketch_path = os.path.join(root, file)
                    relative_path = os.path.relpath(sketch_path, self.results_dir)
                    
                    # Extract concept name from directory structure
                    concept = os.path.basename(root) if root != self.results_dir else file.replace('.png', '')
                    
                    # Get file info
                    stat = os.stat(sketch_path)
                    created_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Look for corresponding SVG and log files
                    base_name = file.replace('.png', '')
                    svg_path = os.path.join(root, f"{base_name}.svg")
                    log_path = os.path.join(root, "experiment_log.json")
                    
                    sketch_info = {
                        'id': relative_path.replace('/', '_').replace('.png', ''),
                        'concept': concept.replace('_', ' ').title(),
                        'filename': file,
                        'path': sketch_path,
                        'relative_path': relative_path,
                        'created': created_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': created_time.timestamp(),
                        'has_svg': os.path.exists(svg_path),
                        'has_log': os.path.exists(log_path),
                        'svg_path': svg_path if os.path.exists(svg_path) else None,
                        'log_path': log_path if os.path.exists(log_path) else None
                    }
                    
                    # Try to get image dimensions
                    try:
                        with Image.open(sketch_path) as img:
                            sketch_info['width'], sketch_info['height'] = img.size
                    except Exception:
                        sketch_info['width'], sketch_info['height'] = 0, 0
                    
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
        
        # Add additional details
        if sketch['has_log']:
            try:
                with open(sketch['log_path'], 'r') as f:
                    log_data = json.load(f)
                    sketch['conversation'] = log_data
            except Exception:
                pass
        
        return sketch
    
    def delete_sketch(self, sketch_id):
        """Delete a sketch and its associated files"""
        sketch = self.get_sketch_details(sketch_id)
        if not sketch:
            return False
        
        try:
            # Delete PNG file
            if os.path.exists(sketch['path']):
                os.remove(sketch['path'])
            
            # Delete SVG file if exists
            if sketch['has_svg'] and os.path.exists(sketch['svg_path']):
                os.remove(sketch['svg_path'])
            
            # Delete log file if exists and it's in the same directory
            if sketch['has_log']:
                sketch_dir = os.path.dirname(sketch['path'])
                log_dir = os.path.dirname(sketch['log_path'])
                if sketch_dir == log_dir and os.path.exists(sketch['log_path']):
                    os.remove(sketch['log_path'])
            
            # Remove directory if empty
            sketch_dir = os.path.dirname(sketch['path'])
            if os.path.exists(sketch_dir) and not os.listdir(sketch_dir):
                os.rmdir(sketch_dir)
            
            return True
        except Exception as e:
            print(f"Error deleting sketch {sketch_id}: {e}")
            return False

# Initialize gallery
gallery = SketchGallery()

@app.route('/')
def gallery_home():
    """Main gallery page"""
    return render_template('gallery.html')

@app.route('/api/sketches')
def api_sketches():
    """API endpoint to get all sketches"""
    sketches = gallery.scan_sketches()
    
    # Add URL paths for web serving
    for sketch in sketches:
        sketch['url'] = f"/sketch-image/{sketch['id']}"
        if sketch['has_svg']:
            sketch['svg_url'] = f"/sketch-svg/{sketch['id']}"
    
    return jsonify(sketches)

@app.route('/api/sketch/<sketch_id>')
def api_sketch_details(sketch_id):
    """API endpoint to get detailed sketch information"""
    sketch = gallery.get_sketch_details(sketch_id)
    if not sketch:
        return jsonify({'error': 'Sketch not found'}), 404
    
    sketch['url'] = f"/sketch-image/{sketch['id']}"
    if sketch['has_svg']:
        sketch['svg_url'] = f"/sketch-svg/{sketch['id']}"
    
    return jsonify(sketch)

@app.route('/api/sketch/<sketch_id>/delete', methods=['POST'])
def api_delete_sketch(sketch_id):
    """API endpoint to delete a sketch"""
    success = gallery.delete_sketch(sketch_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete sketch'}), 500

@app.route('/sketch-image/<sketch_id>')
def serve_sketch_image(sketch_id):
    """Serve sketch PNG images"""
    sketch = gallery.get_sketch_details(sketch_id)
    if not sketch or not os.path.exists(sketch['path']):
        return "Image not found", 404
    
    return send_from_directory(os.path.dirname(sketch['path']), os.path.basename(sketch['path']))

@app.route('/sketch-svg/<sketch_id>')
def serve_sketch_svg(sketch_id):
    """Serve sketch SVG files"""
    sketch = gallery.get_sketch_details(sketch_id)
    if not sketch or not sketch['has_svg'] or not os.path.exists(sketch['svg_path']):
        return "SVG not found", 404
    
    return send_from_directory(os.path.dirname(sketch['svg_path']), os.path.basename(sketch['svg_path']))

if __name__ == '__main__':
    print("🖼️ SketchAgent Gallery")
    print("=" * 40)
    print("Starting gallery server...")
    print("Gallery will be available at: http://localhost:5001")
    print("=" * 40)
    
    # Create template if it doesn't exist
    gallery.ensure_directories()
    
    app.run(debug=True, port=5001, host='0.0.0.0')