# SketchAgent: Language-Driven Sequential Sketch Generation

A Python implementation of SketchAgent that leverages Google Gemini API to facilitate language-driven, sequential sketch generation through an intuitive sketching language. It can sketch diverse concepts, engage in interactive sketching with humans, and edit content via chat.

**🎨 Complete implementation with all features from the original [yael-vinker/SketchAgent](https://github.com/yael-vinker/SketchAgent)**

## ✨ Features

- **📝 Text-to-Sketch**: Generate single sketch by running a command with your concept  
- **🤝 Collaborative Sketching**: Collaborate with SketchAgent by alternating strokes in an interactive web interface
- **💬 Chat-Based Editing**: Interact with SketchAgent through natural language to edit existing sketches
- **🎯 Grid-Based System**: 50x50 grid coordinate system for precise drawing control
- **📊 SVG Generation**: Creates vector sketches that can be animated
- **🖼️ Multiple Formats**: Output in SVG, PNG with/without canvas background

## 🚀 Quick Start

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

### 🔑 API Key Setup

This repository requires a Google Gemini API key. If you don't have one, visit [Google AI Studio](https://makersuite.google.com/app/apikey) to obtain a key.

Once you have the key, copy `.env.example` to `.env` and add your key:
```bash
cp .env.example .env
# Edit .env file and add: GOOGLE_API_KEY=your_actual_api_key
```

### ✅ Test Installation

Run the test suite to verify everything is working:
```bash
python test_implementation.py
```

## 📚 Usage

### 1. 📝 Text-to-Sketch Generation
Generate a single sketch from text:
```bash
python gen_sketch.py --concept_to_draw "sailboat"
python gen_sketch.py --concept_to_draw "house" --seed_mode stochastic
```

**Optional arguments:**
- `--seed_mode`: "deterministic" (default) for reproducible results, "stochastic" for variety
- `--path2save`: Output directory (default: `results/test/`)
- `--model`: Gemini model to use (default: `gemini-1.5-flash`)
- `--res`: Grid resolution (default: 50x50)

### 2. 🤝 Collaborative Sketching
Interactive sketching with alternating user/AI strokes:
```bash
python collab_sketch.py
```
- Launches Flask web application
- Open the provided URL in your browser
- Choose between Solo and Collaborative modes
- Draw strokes and let SketchAgent respond
- Results saved to `results/collab_sketching/`

### 3. 💬 Chat-Based Editing
Natural language sketch editing:
```bash
python chat_and_edit.py
```
- Launches chat interface at `http://localhost:5000`
- Generate initial sketch from text
- Chat to edit: "Add a sun", "Make the cat smile", "Draw a tree"
- Real-time sketch updates based on conversation

## 🏗️ Project Structure

```
sketchagent/
├── gen_sketch.py           # Command-line sketch generation
├── collab_sketch.py        # Interactive collaborative sketching
├── chat_and_edit.py        # Chat-based editing interface
├── utils.py               # Core utilities (grid, SVG, image processing)
├── prompts.py             # AI prompts and examples
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── test_implementation.py # Test suite
├── templates/            # HTML templates
│   ├── index.html       # Collaborative sketching UI
│   └── chat.html        # Chat-based editing UI
├── static/              # Static assets
└── results/             # Generated sketches and logs
```

## 🔧 Technical Details

### Core Components
- **Grid System**: 50x50 coordinate grid for precise drawing control
- **Bezier Curves**: Smooth stroke generation using control points
- **SVG Processing**: Vector-based sketches with animation support
- **XML Format**: Structured stroke data for reproducibility
- **Flask Web Apps**: Modern web interfaces for interaction

### API Integration
- **Google Gemini**: Replaces original Anthropic Claude API
- **Deterministic Mode**: Reproducible results with temperature=0
- **Stochastic Mode**: Creative variety with higher temperature
- **Prompt Engineering**: Optimized for sketch generation tasks

## 🔄 Differences from Original

This implementation maintains **complete feature parity** with [yael-vinker/SketchAgent](https://github.com/yael-vinker/SketchAgent) while making these improvements:

- ✅ **Google Gemini API** instead of Anthropic Claude
- ✅ **Python venv** instead of Conda environment  
- ✅ **Simplified setup** with `requirements.txt`
- ✅ **Enhanced error handling** and user feedback
- ✅ **Comprehensive test suite** for validation
- ✅ **Clear documentation** and examples

## 🧪 Testing

Run tests to verify functionality:
```bash
python test_implementation.py
```

This will test:
- ✅ All imports and dependencies
- ✅ Core utilities functionality  
- ✅ Prompt system
- ✅ File structure
- ✅ Syntax validation

## 🎯 Example Outputs

The system can generate sketches for various concepts:
- 🏠 **Objects**: house, car, tree, flower, cat, dog
- 🌅 **Scenes**: landscape, cityscape, beach, forest
- 🎨 **Abstract**: emotions, concepts, ideas
- 🔄 **Editing**: Add/modify elements via natural language

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Credits

Based on the original SketchAgent research by:
- [Yael Vinker](https://yael-vinker.github.io/website/)
- [Tamar Rott Shaham](https://tamarott.github.io/)  
- [Kristine Zheng](https://kristinezheng.github.io/)
- [Alex Zhao](https://www.linkedin.com/in/alex-zhao-a28b12176/)
- [Judith E Fan](https://profiles.stanford.edu/judith-fan)
- [Antonio Torralba](https://groups.csail.mit.edu/vision/torralbalab/)

📝 **Paper**: [SketchAgent: Language-Driven Sequential Sketch Generation](https://arxiv.org/abs/2411.17673)

This implementation adapts the concept to use Google Gemini API with Python virtual environments while maintaining complete feature compatibility.