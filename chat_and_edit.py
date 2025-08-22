from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import argparse
import traceback
from datetime import datetime
import uuid
import ast
import cairosvg
from xml.dom import minidom
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

import utils
from prompts import sketch_first_prompt, system_prompt, gt_example

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve the chat interface"""
    if not path or path == '' or path == 'index.html':
        return send_from_directory('templates', 'chat.html')
    
    # Try to serve static files
    if path.startswith('static/'):
        return send_from_directory('.', path)
    
    return "Not Found", 404

# Store current sketches in memory
sketches = {}

class SketchApp:
    def __init__(self, args):
        # General
        self.path2save = args.path2save
        self.target_concept = args.concept_to_draw
        self.save_name = args.save_name if hasattr(args, 'save_name') else self.target_concept.replace(" ", "_")
        self.args = args

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
        self.model = genai.GenerativeModel("gemini-1.5-flash")
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
        msg_history=[],
        init_canvas_str=None,
        prefill_msg=None,
        seed_mode="stochastic",
        stop_sequences=None,
        gen_mode="generation"
    ):  
        additional_args = {}
        if stop_sequences:
            additional_args["stop_sequences"] = stop_sequences
        
        content = self.call_llm(system_message, msg, additional_args)
        
        if gen_mode == "completion":
            if prefill_msg:
                content = f"{prefill_msg}{content}"

        # saves to json
        if self.path2save is not None:
            system_message_json = [{"role": "system", "content": system_message}]
            new_msg_history = msg_history + [
                {"role": "user", "content": msg},
                {"role": "assistant", "content": content}
            ]
            with open(f"{self.path2save}/experiment_log.json", 'w') as json_file:
                json.dump(system_message_json + new_msg_history, json_file, indent=4)
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
            svg_path = f"{self.path2save}/{self.save_name}.svg"
            with open(svg_path, "w") as svg_file:
                svg_file.write(model_strokes_svg)
            print(f"SVG saved to: {svg_path}")

            # Convert to PNG with blank background
            png_path = f"{self.path2save}/{self.save_name}.png"
            cairosvg.svg2png(url=svg_path, write_to=png_path, background_color="white")
            print(f"PNG saved to: {png_path}")
            
            # Save with canvas background
            canvas_png_path = f"{self.path2save}/{self.save_name}_canvas.png"
            cairosvg.svg2png(url=svg_path, write_to=canvas_png_path)
            foreground = Image.open(canvas_png_path)
            self.init_canvas.paste(Image.open(canvas_png_path), (0, 0), foreground)
            self.init_canvas.save(canvas_png_path)
            
            # Generate stroke data in XML format
            stroke_data = self.extract_stroke_data_from_llm_output(sketching_commands)
            return stroke_data
            
        except Exception as e:
            print(f"❌ Error during sketch generation: {e}")
            traceback.print_exc()
            raise

    def extract_stroke_data_from_llm_output(self, llm_output):
        """Extract stroke data from LLM output and format as XML."""
        try:
            # Create root XML element
            root = ET.Element("answer")

            # Add concept
            concept_elem = ET.SubElement(root, "concept")
            concept_elem.text = self.target_concept

            # Create strokes element
            strokes_elem = ET.SubElement(root, "strokes")

            import re

            # Pattern to match entire stroke sections
            stroke_pattern = r'<s(\d+)>\s*<points>(.*?)</points>\s*<t_values>(.*?)</t_values>\s*<id>(.*?)</id>\s*</s\1>'

            # Find all stroke matches
            stroke_matches = re.findall(stroke_pattern, llm_output, re.DOTALL | re.IGNORECASE)

            stroke_count = 0
            for match in stroke_matches:
                stroke_num, points, t_values, stroke_id = match

                # Clean and process points
                point_pattern = r"'(x\d+y\d+)'"
                parsed_points = re.findall(point_pattern, points)

                # Clean and process t-values
                parsed_t_values = [val.strip() for val in t_values.split(',')]

                # Create stroke element
                stroke_elem = ET.SubElement(strokes_elem, f"s{stroke_num}")

                # Add points
                points_elem = ET.SubElement(stroke_elem, "points")
                points_elem.text = ", ".join([f"'{p}'" for p in parsed_points])

                # Add t-values
                t_values_elem = ET.SubElement(stroke_elem, "t_values")
                t_values_elem.text = ", ".join(parsed_t_values)

                # Add ID
                id_elem = ET.SubElement(stroke_elem, "id")
                id_elem.text = stroke_id.strip()

                stroke_count += 1

            # If no strokes found, fallback to default
            if stroke_count == 0:
                print("No strokes found. Falling back to default stroke.")
                stroke_elem = ET.SubElement(strokes_elem, "s1")

                points_elem = ET.SubElement(stroke_elem, "points")
                points_elem.text = "'x10y10', 'x40y10', 'x40y40', 'x10y40', 'x10y10'"

                t_values_elem = ET.SubElement(stroke_elem, "t_values")
                t_values_elem.text = "0.00, 0.25, 0.50, 0.75, 1.00"

                id_elem = ET.SubElement(stroke_elem, "id")
                id_elem.text = "fallback_stroke"

            # Format the XML nicely
            xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            return xml_str

        except Exception as e:
            print(f"Error extracting stroke data: {e}")
            traceback.print_exc()
            return self.get_default_stroke_data()

    def get_default_stroke_data(self):
        """Generate default stroke data if extraction fails."""
        root = ET.Element("answer")

        concept_elem = ET.SubElement(root, "concept")
        concept_elem.text = self.target_concept

        strokes_elem = ET.SubElement(root, "strokes")

        # Add a simple placeholder stroke
        stroke1 = ET.SubElement(strokes_elem, "s1")
        points1 = ET.SubElement(stroke1, "points")
        points1.text = "'x10y10', 'x40y10', 'x40y40', 'x10y40', 'x10y10'"
        t_values1 = ET.SubElement(stroke1, "t_values")
        t_values1.text = "0.00, 0.25, 0.50, 0.75, 1.00"
        id1 = ET.SubElement(stroke1, "id")
        id1.text = "outline"

        # Format the XML nicely
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        return xml_str

    def edit_sketch_in_chat_add(self, path_to_data, object_to_edit, add_objects, reflection_prompt, cache=True, seed_mode="deterministic"):
        """
        Method to edit an existing sketch by adding new objects incrementally.
        """
        object_to_edit = object_to_edit.replace(" ", "_")  # Normalise the object name
        output_path = f"{path_to_data}/{object_to_edit}/editing_add"
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Load sketch data
        sketch_rendered, system_prompt_data, msg_history, assistant_prompt = load_sketch_data(path_to_data, object_to_edit, cache)
        with open(f"{output_path}/experiment_log.json", 'w') as json_file:
            system_message_json = [{"role": "system", "content": system_prompt_data}]
            json.dump(system_message_json + msg_history, json_file, indent=4)

        # Save given strokes
        prev_strokes_list_str, prev_t_values_str = utils.parse_xml_string(assistant_prompt, res=self.res)
        if prev_strokes_list_str and prev_t_values_str:
            accum_strokes_list, accum_t_values = ast.literal_eval(prev_strokes_list_str), ast.literal_eval(prev_t_values_str)
        else:
            accum_strokes_list, accum_t_values = [], []
            
        cur_sketch_str = utils.image_to_str(sketch_rendered)

        # Add objects in a loop
        for add_object in add_objects:
            user_edit_prompt = reflection_prompt.format(add_object=add_object, object_to_edit=object_to_edit)

            all_llm_output = self.get_response_from_llm(
                        msg=user_edit_prompt,
                        system_message=system_prompt.format(res=self.res),
                        msg_history=msg_history,
                        init_canvas_str=cur_sketch_str,
                        seed_mode=seed_mode,
                        gen_mode=self.gen_mode
                    )

            strokes_list_str, t_values_str = utils.parse_xml_string(all_llm_output, res=self.res)
            if strokes_list_str and t_values_str:
                strokes_list, t_values = ast.literal_eval(strokes_list_str), ast.literal_eval(t_values_str)

                # Add the new strokes to existing ones:
                accum_strokes_list.extend(strokes_list)
                accum_t_values.extend(t_values)
                
            all_control_points = utils.get_control_points(accum_strokes_list, accum_t_values, self.cells_to_pixels_map)
            model_strokes_svg = utils.format_svg(all_control_points, dim=self.grid_size, stroke_width=self.stroke_width)
            sketch_rendered = save_sketch(model_strokes_svg, output_path, add_object, self.init_canvas)

            cur_sketch_str = utils.image_to_str(sketch_rendered)
            msg_history = msg_history + [
                    {"role": "user", "content": user_edit_prompt},
                    {"role": "assistant", "content": all_llm_output}
                ]

        # Return final results including the new strokes
        return {
            "final_image": sketch_rendered,
            "stroke_data": self.format_stroke_data_for_frontend(accum_strokes_list, accum_t_values, object_to_edit, add_objects)
        }

    def format_stroke_data_for_frontend(self, strokes_list, t_values, original_concept, added_objects):
        """Format stroke data in XML format for frontend animation"""
        root = ET.Element("answer")

        # Add concept
        concept_elem = ET.SubElement(root, "concept")
        concept_elem.text = f"{original_concept} with {', '.join(added_objects)}"

        # Create strokes element
        strokes_elem = ET.SubElement(root, "strokes")

        # Add each stroke to the XML
        for i, (points, t_vals) in enumerate(zip(strokes_list, t_values)):
            stroke_elem = ET.SubElement(strokes_elem, f"s{i+1}")

            # Add points
            points_elem = ET.SubElement(stroke_elem, "points")
            points_elem.text = ", ".join([f"'{p}'" for p in points])

            # Add t-values
            t_values_elem = ET.SubElement(stroke_elem, "t_values")
            t_values_elem.text = ", ".join([str(t) for t in t_vals])

            # Add ID
            id_elem = ET.SubElement(stroke_elem, "id")
            id_elem.text = f"stroke_{i+1}"

        # Format the XML nicely
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        return xml_str

def create_args_for_concept(concept):
    """Create args object similar to what argparse would create"""
    args = argparse.Namespace()

    # General
    args.concept_to_draw = concept
    args.seed_mode = 'deterministic'

    # Create unique folder with absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    session_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    args.path2save = os.path.join(current_dir, f"results/api_{timestamp}_{session_id}")

    args.model = 'gemini-1.5-flash'
    args.gen_mode = 'generation'

    # Grid params
    args.res = 50
    args.cell_size = 12
    args.stroke_width = 7.0
    args.grid_size = (args.res + 1) * args.cell_size

    args.save_name = args.concept_to_draw.replace(" ", "_")
    args.path2save = os.path.join(args.path2save, args.save_name)

    if not os.path.exists(args.path2save):
        os.makedirs(args.path2save)
        with open(os.path.join(args.path2save, "experiment_log.json"), 'w') as json_file:
            json.dump([], json_file, indent=4)

    return args

def load_sketch_data(path_to_data: str, object_to_edit: str, cache: bool = False):
    """Load sketch data for editing"""
    object_dir_name = object_to_edit.replace(" ", "_")
    obj_dir = Path(path_to_data) / object_dir_name

    im_path = obj_dir / f"output_{object_dir_name}_canvas.png"
    if not im_path.exists():
        im_path = obj_dir / f"{object_dir_name}_canvas.png"
    if not im_path.exists():
        im_path = obj_dir / f"{object_dir_name}.png"
        
    json_path = obj_dir / "experiment_log.json"

    if not json_path.exists():
        raise FileNotFoundError(
            f"{json_path} not found.\n"
            f"Available objects in {path_to_data}: "
            f"{[p.name for p in Path(path_to_data).iterdir() if p.is_dir()]}"
        )

    with json_path.open() as f:
        log = json.load(f)

    if len(log) == 0:
        raise ValueError("Empty experiment log")
        
    system_prompt = log[0].get("content", "")
    if isinstance(system_prompt, list):
        system_prompt = system_prompt[0].get("text", "") if system_prompt else ""
        
    assistant_prompt = ""
    msg_history = []
    
    if len(log) > 2:
        assistant_prompt = log[-1].get("content", "")
        if isinstance(assistant_prompt, list):
            assistant_prompt = assistant_prompt[0].get("text", "") if assistant_prompt else ""
        msg_history = log[1:-1] if len(log) > 2 else []

    if im_path.exists():
        sketch_rendered = Image.open(im_path)
    else:
        # Create a blank image if no image found
        sketch_rendered = Image.new('RGB', (612, 612), 'white')
        
    return sketch_rendered, system_prompt, msg_history, assistant_prompt

def save_sketch(model_strokes_svg, output_path, add_object, init_canvas):
    """Save sketch to files"""
    with open(f"{output_path}/output_{add_object}.svg", "w") as svg_file:
        svg_file.write(model_strokes_svg)

    # Save the result with clean white background (no grid)
    cairosvg.svg2png(url=f"{output_path}/output_{add_object}.svg",
                     write_to=f"{output_path}/output_{add_object}.png",
                     background_color="white")

    if init_canvas is not None:
        # For the canvas version, create a blank white canvas instead of using the grid
        output_png_path = f"{output_path}/output_{add_object}_canvas.png"

        # Create a blank white image with the same dimensions as init_canvas
        blank_canvas = Image.new('RGB', init_canvas.size, 'white')

        # Convert SVG to PNG and overlay on blank canvas
        cairosvg.svg2png(url=f"{output_path}/output_{add_object}.svg", write_to=output_png_path)
        foreground = Image.open(output_png_path)
        blank_canvas.paste(foreground, (0, 0), foreground)
        blank_canvas.save(output_png_path)

        return blank_canvas
    
    return Image.open(f"{output_path}/output_{add_object}.png")

@app.route('/generate-sketch', methods=['POST'])
def generate_sketch():
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        if not concept:
            return jsonify({"error": "No concept provided"}), 400

        # Create args for SketchApp
        args = create_args_for_concept(concept)

        # Initialize SketchApp
        sketch_app = SketchApp(args)

        # Generate the sketch and get stroke data
        stroke_data = sketch_app.generate_sketch()

        # Get image path
        image_path = f"{args.path2save}/{args.save_name}.png"
        public_path = f"static/sketches/{args.save_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        # Copy to static folder for serving
        os.makedirs(os.path.dirname(f"static/sketches/"), exist_ok=True)

        # Use PIL to copy the image
        img = Image.open(image_path)
        img.save(public_path)

        # Store information for later modifications
        sketches[concept] = {
            'original_path': image_path,
            'public_path': public_path,
            'args': args
        }

        return jsonify({
            "message": f"Successfully generated sketch of {concept}",
            "image_path": public_path,
            "stroke_data": stroke_data
        })

    except Exception as e:
        print(f"Error generating sketch: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/edit-sketch', methods=['POST'])
def edit_sketch():
    try:
        print("=== Starting edit-sketch endpoint ===")
        data = request.get_json()
        concept = data.get('concept', '')
        objects_to_add = data.get('objects_to_add', [])

        print(f"Request data: concept='{concept}', objects_to_add={objects_to_add}")

        if not concept or not objects_to_add:
            print("Missing required parameters")
            return jsonify({"error": "Both concept and objects_to_add must be provided"}), 400

        # Check if we have this sketch
        if concept not in sketches:
            print(f"Sketch '{concept}' not found in sketches dictionary")
            print(f"Available sketches: {list(sketches.keys())}")
            return jsonify({"error": f"No sketch found for '{concept}'"}), 404

        # Get original sketch info
        original_sketch_info = sketches[concept]
        print(f"Found sketch info: {original_sketch_info}")

        # Get the original image path
        original_image_path = original_sketch_info['original_path']
        print(f"Original image path: {original_image_path}")

        if not os.path.exists(original_image_path):
            print(f"WARNING: Original image does not exist at: {original_image_path}")
            return jsonify({"error": "Original image file not found"}), 500

        # Create a copy of the image for modification
        original_image = Image.open(original_image_path)

        # Create output directory and copy experiment_log.json
        base_dir = os.path.dirname(original_image_path)
        exp_log_path = os.path.join(base_dir, "experiment_log.json")
        if os.path.exists(exp_log_path):
            with open(exp_log_path, 'r') as f:
                experiment_log = json.load(f)

        # Use the SketchApp class method to edit the sketch
        sketch_app = SketchApp(original_sketch_info['args'])
        print(f"Created SketchApp instance")

        # Define reflection prompt
        reflection_prompt = "Please add {add_object} to the existing sketch of {object_to_edit}."

        # Prepare the edit_sketch_in_chat_add parameters
        path_to_data = os.path.dirname(base_dir)

        # Create a simple structure that load_sketch_data expects
        concept_clean = concept.replace(" ", "_")
        output_filename = f"{concept_clean}_canvas.png"
        output_path = os.path.join(path_to_data, concept_clean)
        os.makedirs(output_path, exist_ok=True)

        # Copy the original image to where load_sketch_data expects it
        original_image.save(os.path.join(output_path, output_filename))

        print(f"Set up temporary file at: {os.path.join(output_path, output_filename)}")

        # Now call the edit method
        results = sketch_app.edit_sketch_in_chat_add(
            path_to_data=path_to_data,
            object_to_edit=concept_clean,
            add_objects=objects_to_add,
            reflection_prompt=reflection_prompt,
            cache=False,
            seed_mode="deterministic"
        )

        print(f"Edit sketch results keys: {results.keys() if results else 'None'}")

        # Get the final image and stroke data from the results
        final_image = results.get("final_image")
        stroke_data = results.get("stroke_data")

        if final_image is None:
            print("No final_image in results")
            return jsonify({"error": "Failed to generate edited sketch"}), 500

        # Generate a path for the edited image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        edited_concept = f"{concept} with {', '.join(objects_to_add)}"
        edited_name = edited_concept.replace(" ", "_")

        # Create a path in the static folder
        os.makedirs("static/sketches", exist_ok=True)
        public_path = f"static/sketches/{edited_name}_{timestamp}.png"
        full_public_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), public_path)

        print(f"Will save edited image to {full_public_path}")

        # Save the image
        final_image.save(full_public_path)
        print(f"Image saved")

        # Store the edited sketch info
        sketches[edited_concept] = {
            'original_path': full_public_path,
            'public_path': public_path,
            'args': original_sketch_info['args'],
            'parent_concept': concept
        }

        print("=== Successfully completed edit-sketch endpoint ===")
        return jsonify({
            "message": f"Successfully added {', '.join(objects_to_add)} to sketch of {concept}",
            "image_path": public_path,
            "stroke_data": stroke_data
        })

    except Exception as e:
        print(f"=== ERROR in edit-sketch endpoint: {e} ===")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

def main():
    # Make sure the folder for generated sketches exists
    Path("static/sketches").mkdir(parents=True, exist_ok=True)

    PORT = 5000
    HOST = "0.0.0.0"
    
    try:
        # Get the IP address
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
    except OSError:
        ip_address = "127.0.0.1"

    print(f"\n🎨 SketchAgent - Chat-based Sketch Editing")
    print("=" * 50)
    print(f"Server running at: http://{ip_address}:{PORT}")
    print("=" * 50)

    # Start Flask
    app.run(host=HOST, port=PORT, debug=True)

if __name__ == "__main__":
    main()