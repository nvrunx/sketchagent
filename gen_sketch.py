import argparse
import google.generativeai as genai
import ast
import json
import os
import utils
import traceback
from svg_converter import svg2png

from dotenv import load_dotenv
from PIL import Image
from prompts import sketch_first_prompt, system_prompt, gt_example


def call_argparse():
    parser = argparse.ArgumentParser(description='Generate sketches using Google Gemini API')
    
    # General
    parser.add_argument('--concept_to_draw', type=str, default="cat", help="Concept to draw")
    parser.add_argument('--seed_mode', type=str, default='deterministic', choices=['deterministic', 'stochastic'], help="Generation mode")
    parser.add_argument('--path2save', type=str, default=f"results/test", help="Path to save results")
    parser.add_argument('--model', type=str, default='gemini-1.5-flash', help="Gemini model to use")
    parser.add_argument('--gen_mode', type=str, default='generation', choices=['generation', 'completion'], help="Generation mode")

    # Grid params
    parser.add_argument('--res', type=int, default=50, help="Grid resolution (50x50)")
    parser.add_argument('--cell_size', type=int, default=12, help="Size of each cell in pixels")
    parser.add_argument('--stroke_width', type=float, default=7.0, help="SVG stroke width")

    args = parser.parse_args()
    args.grid_size = (args.res + 1) * args.cell_size

    args.save_name = args.concept_to_draw.replace(" ", "_")
    args.path2save = f"{args.path2save}/{args.save_name}"
    if not os.path.exists(args.path2save):
        os.makedirs(args.path2save)
        with open(f"{args.path2save}/experiment_log.json", 'w') as json_file:
            json.dump([], json_file, indent=4)
    return args


class SketchApp:
    def __init__(self, args):
        # General
        self.path2save = args.path2save
        self.target_concept = args.concept_to_draw

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
        
        # LLM Setup (you need to provide your GOOGLE_API_KEY in your .env file)
        self.cache = False
        self.max_tokens = 8192
        load_dotenv()
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")
        
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel(args.model)
        self.input_prompt = sketch_first_prompt.format(concept=args.concept_to_draw, gt_sketches_str=gt_example)
        self.gen_mode = args.gen_mode
        self.seed_mode = args.seed_mode
        

    def call_llm(self, system_message, user_message, additional_args):
        """Call Gemini API with system message and user message"""
        try:
            # Combine system message and user message for Gemini
            combined_prompt = f"{system_message}\n\nUser: {user_message}"
            
            # Set generation config based on seed mode
            generation_config = {}
            if self.seed_mode == "deterministic":
                generation_config["temperature"] = 0.0
                generation_config["top_k"] = 1
                generation_config["top_p"] = 1.0
            else:
                generation_config["temperature"] = 0.7
            
            if "max_output_tokens" not in generation_config:
                generation_config["max_output_tokens"] = self.max_tokens
            
            # Add any additional args to generation config
            generation_config.update(additional_args.get("generation_config", {}))
            
            response = self.model.generate_content(
                combined_prompt,
                generation_config=genai.GenerationConfig(**generation_config)
            )
            
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            raise


    def get_response_from_llm(
        self,
        msg,
        system_message,
        seed_mode="stochastic",
        stop_sequences=None,
        gen_mode="generation"
    ):  
        additional_args = {}
        if stop_sequences:
            additional_args["stop_sequences"] = stop_sequences
        
        content = self.call_llm(system_message, msg, additional_args)
        
        # Save to json
        if self.path2save is not None:
            conversation_log = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": msg},
                {"role": "assistant", "content": content}
            ]
            with open(f"{self.path2save}/experiment_log.json", 'w') as json_file:
                json.dump(conversation_log, json_file, indent=4)
            print(f"Data has been saved to [{self.path2save}/experiment_log.json]")
            
        return content


    def call_model_for_sketch_generation(self):
        print("Calling Gemini API for sketch generation...")
        print(f"Input Prompt: {self.input_prompt[:200]}...")

        try:
            all_llm_output = self.get_response_from_llm(
                msg=self.input_prompt,
                system_message=system_prompt.format(res=self.res),
                seed_mode=self.seed_mode,
                gen_mode=self.gen_mode
            )

            print("LLM Output received successfully")
            print(f"Output length: {len(all_llm_output)} characters")
            
            # Ensure the output ends with </answer> for parsing
            if "</answer>" not in all_llm_output:
                all_llm_output += "</answer>"

            return all_llm_output
            
        except Exception as e:
            print(f"Error in LLM call: {e}")
            import traceback
            traceback.print_exc()
            raise
        

    def parse_model_to_svg(self, model_rep_sketch):
        # Parse model_rep with xml
        strokes_list_str, t_values_str = utils.parse_xml_string(model_rep_sketch, self.res)
        
        if strokes_list_str is None or t_values_str is None:
            print("Error: Could not parse XML string")
            print("Raw output:", model_rep_sketch[:500])
            raise ValueError("Failed to parse LLM output as XML")
            
        strokes_list, t_values = ast.literal_eval(strokes_list_str), ast.literal_eval(t_values_str)

        # extract control points from sampled lists
        all_control_points = utils.get_control_points(strokes_list, t_values, self.cells_to_pixels_map)

        # define SVG based on control point
        sketch_text_svg = utils.format_svg(all_control_points, dim=self.grid_size, stroke_width=self.stroke_width)
        return sketch_text_svg
        

    def generate_sketch(self):
        try:
            print(f"Starting sketch generation for concept: {self.target_concept}")
            
            sketching_commands = self.call_model_for_sketch_generation()
            print("Converting to SVG...")
            
            model_strokes_svg = self.parse_model_to_svg(sketching_commands)
            
            # Save the SVG sketch
            svg_path = f"{self.path2save}/{self.target_concept}.svg"
            with open(svg_path, "w") as svg_file:
                svg_file.write(model_strokes_svg)
            print(f"SVG saved to: {svg_path}")

            # Convert to PNG with blank background
            png_path = f"{self.path2save}/{self.target_concept}.png"
            svg2png(url=svg_path, write_to=png_path, background_color="white")
            print(f"PNG saved to: {png_path}")
            
            # Save the sketch to PNG on the canvas
            output_png_path = f"{self.path2save}/{self.target_concept}_canvas.png"
            svg2png(url=svg_path, write_to=output_png_path)
            foreground = Image.open(output_png_path)
            self.init_canvas.paste(Image.open(output_png_path), (0, 0), foreground) 
            self.init_canvas.save(output_png_path)
            print(f"Canvas PNG saved to: {output_png_path}")
            
            print(f"✅ Sketch generation completed successfully!")
            print(f"📁 Results saved in: {self.path2save}")
            
        except Exception as e:
            print(f"❌ Error during sketch generation: {e}")
            traceback.print_exc()
            raise


# Initialize and run the SketchApp
if __name__ == '__main__':
    print("🎨 SketchAgent - Text-to-Sketch Generation")
    print("=" * 50)
    
    try:
        args = call_argparse()
        print(f"Concept to draw: {args.concept_to_draw}")
        print(f"Seed mode: {args.seed_mode}")
        print(f"Model: {args.model}")
        print(f"Grid resolution: {args.res}x{args.res}")
        print("=" * 50)
        
        sketch_app = SketchApp(args)
        
        # Try up to 3 times in case of failures
        for attempt in range(3):
            try:
                print(f"Attempt {attempt + 1}/3")
                sketch_app.generate_sketch()
                print("🎉 Success!")
                break
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    print("💀 All attempts failed. Please check your API key and try again.")
                    raise
                print("🔄 Retrying...")
                
    except KeyboardInterrupt:
        print("\n⏹️ Generation cancelled by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        exit(1)