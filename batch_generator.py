#!/usr/bin/env python3
"""
SketchAgent Batch Generator - Generate multiple concepts efficiently
"""

import argparse
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enhanced_gen_sketch import EnhancedSketchApp
from enhanced_utils import COLOR_PALETTES, DRAWING_STYLES


def create_args(concept, palette, style, variations=1, output_dir="results/batch"):
    """Create arguments object for a single generation task"""
    class Args:
        def __init__(self):
            self.concept_to_draw = concept
            self.color_palette = palette
            self.drawing_style = style
            self.enable_colors = True
            self.num_variations = variations
            self.seed_mode = 'stochastic'
            self.model = 'gemini-1.5-flash'
            self.gen_mode = 'generation'
            self.res = 50
            self.cell_size = 12
            self.stroke_width = 7.0
            self.grid_size = (self.res + 1) * self.cell_size
            self.save_name = concept.replace(" ", "_")
            self.path2save = f"{output_dir}/{concept.replace(' ', '_')}_{palette}_{style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return Args()


def generate_single_concept(task_info):
    """Generate sketches for a single concept"""
    concept, palette, style, variations = task_info
    
    try:
        print(f"🎨 Starting: {concept} ({palette} palette, {style} style)")
        
        args = create_args(concept, palette, style, variations)
        sketch_app = EnhancedSketchApp(args)
        
        results = sketch_app.generate_sketches()
        
        return {
            'concept': concept,
            'palette': palette,
            'style': style,
            'variations': variations,
            'status': 'success',
            'results': results,
            'output_path': args.path2save
        }
        
    except Exception as e:
        print(f"❌ Error generating {concept}: {e}")
        return {
            'concept': concept,
            'palette': palette,
            'style': style,
            'variations': variations,
            'status': 'error',
            'error': str(e)
        }


class BatchGenerator:
    def __init__(self, output_dir="results/batch", max_workers=2):
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.ensure_directories()
    
    def ensure_directories(self):
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_from_list(self, concepts, palette='vibrant', style='sketch', variations=1):
        """Generate sketches for a list of concepts"""
        tasks = [(concept, palette, style, variations) for concept in concepts]
        return self.generate_batch(tasks)
    
    def generate_style_variations(self, concept, palettes=None, styles=None, variations=1):
        """Generate the same concept in different styles and palettes"""
        if palettes is None:
            palettes = ['vibrant', 'nature', 'sunset']
        if styles is None:
            styles = ['sketch', 'cartoon', 'watercolor']
        
        tasks = []
        for palette in palettes:
            for style in styles:
                tasks.append((concept, palette, style, variations))
        
        return self.generate_batch(tasks)
    
    def generate_theme_collection(self, theme_name, theme_concepts, palette='vibrant', style='sketch', variations=1):
        """Generate a themed collection of sketches"""
        print(f"🎭 Generating {theme_name} theme collection")
        print(f"📋 Concepts: {', '.join(theme_concepts)}")
        
        tasks = [(concept, palette, style, variations) for concept in theme_concepts]
        results = self.generate_batch(tasks)
        
        # Save theme collection summary
        collection_summary = {
            'theme_name': theme_name,
            'concepts': theme_concepts,
            'palette': palette,
            'style': style,
            'variations_per_concept': variations,
            'generated_at': datetime.now().isoformat(),
            'results': results
        }
        
        summary_path = f"{self.output_dir}/{theme_name}_collection.json"
        with open(summary_path, 'w') as f:
            json.dump(collection_summary, f, indent=4)
        
        print(f"📄 Collection summary saved: {summary_path}")
        return results
    
    def generate_batch(self, tasks):
        """Generate multiple sketch tasks in parallel"""
        print(f"🚀 Starting batch generation of {len(tasks)} tasks")
        print(f"🔧 Using {self.max_workers} worker threads")
        print("=" * 60)
        
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {executor.submit(generate_single_concept, task): task for task in tasks}
            
            # Process completed tasks
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if result['status'] == 'success':
                        print(f"✅ {completed}/{len(tasks)} - {result['concept']} completed")
                    else:
                        print(f"❌ {completed}/{len(tasks)} - {result['concept']} failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as exc:
                    print(f"❌ Task {task[0]} generated an exception: {exc}")
                    results.append({
                        'concept': task[0],
                        'palette': task[1],
                        'style': task[2],
                        'status': 'error',
                        'error': str(exc)
                    })
                    completed += 1
        
        # Generate batch summary
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']
        
        print("=" * 60)
        print(f"🎉 Batch generation completed!")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"📁 Output directory: {self.output_dir}")
        
        # Save batch summary
        batch_summary = {
            'total_tasks': len(tasks),
            'successful': len(successful),
            'failed': len(failed),
            'generated_at': datetime.now().isoformat(),
            'results': results
        }
        
        summary_path = f"{self.output_dir}/batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(batch_summary, f, indent=4)
        
        print(f"📄 Batch summary saved: {summary_path}")
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Batch generate multiple sketches')
    parser.add_argument('--mode', type=str, choices=['list', 'styles', 'theme'], default='list',
                       help='Generation mode')
    parser.add_argument('--concepts', nargs='+', 
                       help='List of concepts to generate (for list mode)')
    parser.add_argument('--concept', type=str,
                       help='Single concept for style variations')
    parser.add_argument('--theme', type=str,
                       help='Theme name for collection mode')
    parser.add_argument('--theme_concepts', nargs='+',
                       help='Concepts for theme collection')
    parser.add_argument('--palette', type=str, default='vibrant',
                       choices=list(COLOR_PALETTES.keys()),
                       help='Color palette')
    parser.add_argument('--style', type=str, default='sketch',
                       choices=list(DRAWING_STYLES.keys()),
                       help='Drawing style')
    parser.add_argument('--palettes', nargs='+',
                       choices=list(COLOR_PALETTES.keys()),
                       help='Multiple palettes for style variations')
    parser.add_argument('--styles', nargs='+',
                       choices=list(DRAWING_STYLES.keys()),
                       help='Multiple styles for style variations')
    parser.add_argument('--variations', type=int, default=1,
                       help='Variations per concept')
    parser.add_argument('--output_dir', type=str, default='results/batch',
                       help='Output directory')
    parser.add_argument('--max_workers', type=int, default=2,
                       help='Maximum worker threads')
    
    args = parser.parse_args()
    
    print("🎨 SketchAgent Batch Generator")
    print("=" * 40)
    
    generator = BatchGenerator(args.output_dir, args.max_workers)
    
    if args.mode == 'list':
        if not args.concepts:
            print("❌ Error: --concepts required for list mode")
            return
        
        print(f"📋 Mode: Generate list of concepts")
        print(f"🎨 Concepts: {', '.join(args.concepts)}")
        print(f"🎭 Style: {args.style}")
        print(f"🎨 Palette: {args.palette}")
        
        results = generator.generate_from_list(
            args.concepts, args.palette, args.style, args.variations
        )
        
    elif args.mode == 'styles':
        if not args.concept:
            print("❌ Error: --concept required for styles mode")
            return
        
        palettes = args.palettes or ['vibrant', 'nature', 'sunset']
        styles = args.styles or ['sketch', 'cartoon', 'watercolor']
        
        print(f"📋 Mode: Style variations")
        print(f"🎨 Concept: {args.concept}")
        print(f"🎭 Styles: {', '.join(styles)}")
        print(f"🎨 Palettes: {', '.join(palettes)}")
        
        results = generator.generate_style_variations(
            args.concept, palettes, styles, args.variations
        )
        
    elif args.mode == 'theme':
        if not args.theme or not args.theme_concepts:
            print("❌ Error: --theme and --theme_concepts required for theme mode")
            return
        
        print(f"📋 Mode: Theme collection")
        print(f"🎭 Theme: {args.theme}")
        
        results = generator.generate_theme_collection(
            args.theme, args.theme_concepts, args.palette, args.style, args.variations
        )
    
    print("\n🎉 All done! Check the output directory for results.")


# Predefined theme collections
THEME_COLLECTIONS = {
    'animals': ['cat', 'dog', 'bird', 'fish', 'butterfly', 'elephant'],
    'nature': ['tree', 'flower', 'mountain', 'river', 'sunset', 'cloud'],
    'objects': ['house', 'car', 'chair', 'book', 'lamp', 'clock'],
    'food': ['apple', 'pizza', 'cake', 'coffee', 'bread', 'banana'],
    'fantasy': ['dragon', 'unicorn', 'wizard', 'castle', 'magic wand', 'fairy']
}

if __name__ == '__main__':
    print("Available theme collections:")
    for theme, concepts in THEME_COLLECTIONS.items():
        print(f"  {theme}: {', '.join(concepts)}")
    print()
    
    main()