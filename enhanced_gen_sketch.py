#!/usr/bin/env python3
"""
Enhanced SketchAgent with color and style support
"""

import argparse
import google.generativeai as genai
import ast
import cairosvg
import json
import os
import utils
import traceback
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
from prompts import sketch_first_prompt, system_prompt, gt_example
from enhanced_utils import (
    COLOR_PALETTES, DRAWING_STYLES, get_palette_colors, get_style_config,
    choose_colors_for_concept, format_colored_svg, enhance_sketch_prompt
)


def call_argparse():
    parser = argparse.ArgumentParser(description='Generate enhanced sketches with color and style support')
    
    # General
    parser.add_argument('--concept_to_draw', type=str, default="cat", help="Concept to draw")
    parser.add_argument('--seed_mode', type=str, default='deterministic', choices=['deterministic', 'stochastic'], help="Generation mode")
    parser.add_argument('--path2save', type=str, default=f"results/enhanced", help="Path to save results")
    parser.add_argument('--model', type=str, default='gemini-1.5-flash', help="Gemini model to use")
    parser.add_argument('--gen_mode', type=str, default='generation', choices=['generation', 'completion'], help="Generation mode")

    # Enhanced features
    parser.add_argument('--color_palette', type=str, default='vibrant', 
                       choices=list(COLOR_PALETTES.keys()), 
                       help="Color palette to use")
    parser.add_argument('--drawing_style', type=str, default='sketch', 
                       choices=list(DRAWING_STYLES.keys()), 
                       help="Drawing style to apply")
    parser.add_argument('--enable_colors', action='store_true', default=True, 
                       help="Enable colored output (default: True)")
    parser.add_argument('--num_variations', type=int, default=1, 
                       help="Number of variations to generate")

    # Grid params
    parser.add_argument('--res', type=int, default=50, help="Grid resolution (50x50)")
    parser.add_argument('--cell_size', type=int, default=12, help="Size of each cell in pixels")
    parser.add_argument('--stroke_width', type=float, default=7.0, help="Base SVG stroke width")

    args = parser.parse_args()
    args.grid_size = (args.res + 1) * args.cell_size

    # Create save directory with style and palette info
    args.save_name = args.concept_to_draw.replace(" ", "_")
    if args.enable_colors:
        args.path2save = f"{args.path2save}/{args.save_name}_{args.color_palette}_{args.drawing_style}"
    else:
        args.path2save = f"{args.path2save}/{args.save_name}_{args.drawing_style}"
        
    if not os.path.exists(args.path2save):
        os.makedirs(args.path2save)
        
    return args


class EnhancedSketchApp:
    def __init__(self, args):
        # General
        self.path2save = args.path2save
        self.target_concept = args.concept_to_draw
        self.args = args

        # Enhanced features
        self.color_palette = args.color_palette
        self.drawing_style = args.drawing_style
        self.enable_colors = args.enable_colors
        self.num_variations = args.num_variations

        # Grid related
        self.res = args.res
        self.num_cells = args.res
        self.cell_size = args.cell_size
        self.grid_size = (args.grid_size, args.grid_size)
        self.init_canvas, self.positions = utils.create_grid_image(res=args.res, cell_size=args.cell_size, header_size=args.cell_size)
        self.init_canvas_str = utils.image_to_str(self.init_canvas)
        self.cells_to_pixels_map = utils.cells_to_pixels(args.res, args.cell_size, header_size=args.cell_size)

        # SVG related 
        self.stroke_width = args.stroke_width
        
        # Get colors for this concept and palette
        if self.enable_colors:
            self.colors = choose_colors_for_concept(self.target_concept, self.color_palette)
        else:
            self.colors = {'outline': '#000000', 'fill': 'none', 'accent': '#666666'}
        
        # LLM Setup
        self.cache = False
        self.max_tokens = 8192
        load_dotenv()
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")
        
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel(args.model)
        
        # Enhanced prompt with color and style information
        base_prompt = sketch_first_prompt.format(concept=args.concept_to_draw, gt_sketches_str=gt_example)
        if self.enable_colors:
            self.input_prompt = enhance_sketch_prompt(base_prompt, self.color_palette, self.drawing_style)
        else:
            self.input_prompt = base_prompt
            
        self.gen_mode = args.gen_mode
        self.seed_mode = args.seed_mode
        
        # Save configuration
        self.save_config()

    def save_config(self):
        """Save the generation configuration"""
        config = {
            'concept': self.target_concept,
            'color_palette': self.color_palette,
            'drawing_style': self.drawing_style,
            'enable_colors': self.enable_colors,
            'num_variations': self.num_variations,
            'colors_used': self.colors,
            'grid_resolution': self.res,
            'timestamp': datetime.now().isoformat(),
            'style_config': get_style_config(self.drawing_style),
            'palette_colors': get_palette_colors(self.color_palette)
        }
        
        with open(f"{self.path2save}/generation_config.json", 'w') as f:
            json.dump(config, f, indent=4)

    def call_llm(self, system_message, user_message, additional_args):
        """Call Gemini API with system message and user message"""
        try:
            combined_prompt = f"{system_message}\n\nUser: {user_message}"
            
            generation_config = {}
            if self.seed_mode == "deterministic":
                generation_config["temperature"] = 0.0
                generation_config["top_k"] = 1
                generation_config["top_p"] = 1.0
            else:
                generation_config["temperature"] = 0.7
            
            if "max_output_tokens" not in generation_config:
                generation_config["max_output_tokens"] = self.max_tokens
            
            generation_config.update(additional_args.get("generation_config", {}))
            
            response = self.model.generate_content(
                combined_prompt,
                generation_config=genai.GenerationConfig(**generation_config)
            )
            
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            raise

    def get_response_from_llm(self, msg, system_message, seed_mode="stochastic", stop_sequences=None, gen_mode="generation", variation_num=0):  
        additional_args = {}
        if stop_sequences:
            additional_args["stop_sequences"] = stop_sequences
        
        content = self.call_llm(system_message, msg, additional_args)
        
        # Save to json with variation number
        if self.path2save is not None:
            conversation_log = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": msg},
                {"role": "assistant", "content": content}
            ]
            log_filename = f"experiment_log_v{variation_num}.json" if variation_num > 0 else "experiment_log.json"
            with open(f"{self.path2save}/{log_filename}", 'w') as json_file:
                json.dump(conversation_log, json_file, indent=4)
                
        return content

    def call_model_for_sketch_generation(self, variation_num=0):
        print(f"Calling Gemini API for sketch generation (variation {variation_num + 1}/{self.num_variations})...")
        
        # Add variation instruction for stochastic mode
        input_prompt = self.input_prompt
        if variation_num > 0 and self.seed_mode == "stochastic":
            input_prompt += f"\n\nGenerate a unique variation of this {self.target_concept}. Make it different from previous attempts while maintaining the same concept."

        try:
            all_llm_output = self.get_response_from_llm(
                msg=input_prompt,
                system_message=system_prompt.format(res=self.res),
                seed_mode=self.seed_mode,
                gen_mode=self.gen_mode,
                variation_num=variation_num
            )

            if "</answer>" not in all_llm_output:
                all_llm_output += "</answer>"

            return all_llm_output
            
        except Exception as e:
            print(f"Error in LLM call: {e}")
            traceback.print_exc()
            raise

    def parse_model_to_svg(self, model_rep_sketch, variation_num=0):
        # Parse model_rep with xml
        strokes_list_str, t_values_str = utils.parse_xml_string(model_rep_sketch, self.res)
        
        if strokes_list_str is None or t_values_str is None:
            print("Error: Could not parse XML string")
            raise ValueError("Failed to parse LLM output as XML")
            
        strokes_list, t_values = ast.literal_eval(strokes_list_str), ast.literal_eval(t_values_str)

        # extract control points from sampled lists
        all_control_points = utils.get_control_points(strokes_list, t_values, self.cells_to_pixels_map)

        # Create enhanced SVG with colors and style
        if self.enable_colors:
            sketch_svg = format_colored_svg(all_control_points, dim=self.grid_size, colors=self.colors, style=self.drawing_style)
        else:
            sketch_svg = utils.format_svg(all_control_points, dim=self.grid_size, stroke_width=self.stroke_width)
            
        return sketch_svg

    def generate_sketch_variation(self, variation_num=0):
        """Generate a single sketch variation"""
        print(f"Generating variation {variation_num + 1}...")
        
        try:
            sketching_commands = self.call_model_for_sketch_generation(variation_num)
            model_strokes_svg = self.parse_model_to_svg(sketching_commands, variation_num)
            
            # File naming
            if variation_num > 0:
                base_name = f"{self.target_concept}_v{variation_num + 1}"
            else:
                base_name = self.target_concept
            
            # Save SVG
            svg_path = f"{self.path2save}/{base_name}.svg"
            with open(svg_path, "w") as svg_file:
                svg_file.write(model_strokes_svg)
            print(f"SVG saved to: {svg_path}")

            # Convert to PNG with transparent background
            png_path = f"{self.path2save}/{base_name}.png"
            
            # Choose background color based on palette
            if self.enable_colors:
                palette_info = get_palette_colors(self.color_palette)
                bg_color = palette_info.get('background', 'white')
            else:
                bg_color = 'white'
                
            cairosvg.svg2png(url=svg_path, write_to=png_path, background_color=bg_color)
            print(f"PNG saved to: {png_path}")
            
            # Save on canvas (grid background)
            canvas_png_path = f"{self.path2save}/{base_name}_canvas.png"
            cairosvg.svg2png(url=svg_path, write_to=canvas_png_path)
            foreground = Image.open(canvas_png_path)
            canvas_copy = self.init_canvas.copy()
            canvas_copy.paste(foreground, (0, 0), foreground)
            canvas_copy.save(canvas_png_path)
            print(f"Canvas PNG saved to: {canvas_png_path}")
            
            return {
                'svg_path': svg_path,
                'png_path': png_path, 
                'canvas_path': canvas_png_path,
                'variation': variation_num + 1
            }
            
        except Exception as e:
            print(f"❌ Error generating variation {variation_num + 1}: {e}")
            traceback.print_exc()
            return None

    def generate_sketches(self):
        """Generate all requested sketch variations"""
        print(f"🎨 Starting enhanced sketch generation")
        print(f"📋 Concept: {self.target_concept}")
        print(f"🎨 Style: {self.drawing_style}")
        print(f"🎭 Palette: {self.color_palette}")
        print(f"🔢 Variations: {self.num_variations}")
        print("=" * 60)
        
        results = []
        success_count = 0
        
        for i in range(self.num_variations):
            try:
                result = self.generate_sketch_variation(i)
                if result:
                    results.append(result)
                    success_count += 1
                    print(f"✅ Variation {i + 1} completed successfully!")
                else:
                    print(f"❌ Variation {i + 1} failed")
            except Exception as e:
                print(f"❌ Variation {i + 1} failed with error: {e}")
                continue
        
        print("=" * 60)
        print(f"🎉 Generation completed! {success_count}/{self.num_variations} variations successful")
        print(f"📁 Results saved in: {self.path2save}")
        
        # Save summary
        summary = {
            'concept': self.target_concept,
            'style': self.drawing_style,
            'palette': self.color_palette,
            'total_variations': self.num_variations,
            'successful_variations': success_count,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(f"{self.path2save}/generation_summary.json", 'w') as f:
            json.dump(summary, f, indent=4)
            
        return results


def main():
    print("🎨 Enhanced SketchAgent - Color & Style Generation")
    print("=" * 60)
    
    try:
        args = call_argparse()
        
        print(f"📋 Configuration:")
        print(f"  Concept: {args.concept_to_draw}")
        print(f"  Style: {args.drawing_style} ({DRAWING_STYLES[args.drawing_style]['name']})")
        print(f"  Palette: {args.color_palette}")
        print(f"  Colors enabled: {args.enable_colors}")
        print(f"  Variations: {args.num_variations}")
        print(f"  Model: {args.model}")
        print(f"  Seed mode: {args.seed_mode}")
        print("=" * 60)
        
        sketch_app = EnhancedSketchApp(args)
        results = sketch_app.generate_sketches()
        
        if results:
            print("\n🖼️ Generated files:")
            for result in results:
                print(f"  📄 SVG: {result['svg_path']}")
                print(f"  🖼️ PNG: {result['png_path']}")
                print(f"  📋 Canvas: {result['canvas_path']}")
                print()
                
    except KeyboardInterrupt:
        print("\n⏹️ Generation cancelled by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()