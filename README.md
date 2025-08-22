# SketchAgent: Language-Driven Sequential Sketch Generation

A Python implementation of SketchAgent that leverages Google Gemini API to facilitate language-driven, sequential sketch generation through an intuitive sketching language. It can sketch diverse concepts, engage in interactive sketching with humans, and edit content via chat.

## Features

- **Text-to-Sketch**: Generate single sketch by running a command with your concept
- **Collaborative Sketching**: Collaborate with SketchAgent by alternating strokes in an interactive web interface
- **Chat-Based Editing**: Interact with SketchAgent through natural language to edit existing sketches

## Setup

Clone the repository and navigate to the project folder:
```bash
git clone https://github.com/nvrunx/sketchagent.git
cd sketchagent
```

Set up Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### API Key

This repository requires a Google Gemini API key. If you don't have one, visit [Google AI Studio](https://makersuite.google.com/app/apikey) to obtain a key.

Once you have the key, copy `.env.example` to `.env` and add your key:
```bash
cp .env.example .env
# Edit .env file and add: GOOGLE_API_KEY=your_actual_api_key
```

## Usage

### Text-to-Sketch
Generate a single sketch by running:
```bash
python gen_sketch.py --concept_to_draw "sailboat"
```

Optional arguments:
- `--seed_mode`: Default is "deterministic" for reproducible results. Set to "stochastic" for increased variability.
- `--path2save`: By default, results are saved to `results/test/`.

### Collaborative Sketching
Collaborate with SketchAgent by alternating strokes:
```bash
python collab_sketch.py
```
This will launch a Flask-based web application. Open the provided URL in your web browser to interact with the application. Results are saved to `results/collab_sketching/`.

### Chat-Based Editing
Interact with SketchAgent through natural language to edit existing sketches:
```bash
python chat_and_edit.py
```
This will launch a Flask-based web application for chat-based editing. You can give textual instructions to edit specific sketch elements and add new elements through natural conversation.

## Project Structure

- `gen_sketch.py`: Command-line sketch generation
- `collab_sketch.py`: Interactive collaborative sketching web app
- `chat_and_edit.py`: Chat-based editing web app
- `utils.py`: Utility functions for grid processing, SVG generation, and image handling
- `prompts.py`: System prompts and examples for the AI model
- `templates/`: HTML templates for web interfaces
- `static/`: Static files for web interfaces

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Based on the original SketchAgent by Yael Vinker et al. This implementation adapts the concept to use Google Gemini API instead of Anthropic Claude.