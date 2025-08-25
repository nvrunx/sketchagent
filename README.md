# SketchAgent: Language-Driven Sequential Sketch Generation

A Python implementation of SketchAgent that leverages Google Gemini API to facilitate language-driven, sequential sketch generation through an intuitive sketching language. It can sketch diverse concepts, engage in interactive sketching with humans, and edit content via chat.

**🎨 Complete implementation with all features from the original [yael-vinker/SketchAgent](https://github.com/yael-vinker/SketchAgent)**

## ✨ Features

### **🎨 Enhanced Generation (NEW!)**
- **6 Color Palettes**: Vibrant, Nature, Sunset, Ocean, Pastel, Monochrome
- **5 Drawing Styles**: Sketch, Cartoon, Watercolor, Minimalist, Artistic
- **Multiple Variations**: Generate 1-5 variations of the same concept
- **Smart Coloring**: Context-aware color selection for different concepts

### **🖼️ Gallery System (NEW!)**
- **Browse & Manage**: View all generated sketches in a beautiful gallery
- **Search & Filter**: Find sketches by concept, style, or creation date
- **Detailed View**: See generation parameters and conversation logs
- **Export Options**: Download PNG, SVG, or canvas versions

### **⚡ Batch Processing (NEW!)**
- **Multiple Concepts**: Generate many sketches at once
- **Theme Collections**: Pre-defined collections (animals, nature, etc.)
- **Style Variations**: Same concept in different styles and palettes
- **Parallel Processing**: Efficient multi-threaded generation

### **📊 Progress Tracking (NEW!)**
- **Real-time Progress**: See generation progress with live updates
- **Task History**: Keep track of all generation tasks
- **Statistics Dashboard**: Analytics on usage patterns and success rates
- **Activity Timeline**: Visual history of your sketch creation

### **Original Features**
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

### ⭐ **NEW: Try the Enhanced Studio Interface**
```bash
python studio.py
# Open http://localhost:5002 for the complete interface
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

### 🎨 **NEW: Enhanced Studio Interface**
The all-in-one web interface combining all features:
```bash
python studio.py
# Open http://localhost:5002
```

**Features:**
- 🏠 **Home Dashboard**: Statistics and quick access to features
- ✨ **Enhanced Generation**: Create sketches with colors and styles
- 🖼️ **Gallery**: Browse, search, and manage all your sketches

### ⚡ **NEW: Enhanced Command-Line Generation**
Create sketches with advanced options:
```bash
# Basic enhanced generation
python enhanced_gen_sketch.py --concept_to_draw "butterfly" --color_palette nature --drawing_style watercolor

# Generate multiple variations
python enhanced_gen_sketch.py --concept_to_draw "cat" --num_variations 3 --drawing_style cartoon --color_palette vibrant

# Available palettes: vibrant, nature, sunset, ocean, pastel, monochrome
# Available styles: sketch, cartoon, watercolor, minimalist, artistic
```

### 🚀 **NEW: Batch Generation**
Generate multiple sketches efficiently:
```bash
# Generate multiple concepts
python batch_generator.py --mode list --concepts cat dog bird --palette nature --style sketch

# Generate style variations of one concept  
python batch_generator.py --mode styles --concept house --palettes vibrant sunset --styles sketch cartoon watercolor

# Generate themed collections
python batch_generator.py --mode theme --theme animals --theme_concepts cat dog bird fish butterfly elephant
```

### 🖼️ **NEW: Gallery Management**
Standalone gallery interface:
```bash
python gallery.py
# Open http://localhost:5001
```

### 1. 📝 Original Text-to-Sketch Generation
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
├── 🎨 Enhanced Generation
│   ├── enhanced_gen_sketch.py    # Enhanced generation with colors & styles
│   ├── enhanced_utils.py         # Color palettes and style definitions
│   └── batch_generator.py        # Batch processing for multiple sketches
├── 🖼️ Web Interfaces
│   ├── studio.py                 # All-in-one studio interface
│   ├── gallery.py                # Gallery management system
│   ├── collab_sketch.py          # Interactive collaborative sketching
│   └── chat_and_edit.py          # Chat-based editing interface
├── 📊 Core System
│   ├── gen_sketch.py             # Original command-line generation
│   ├── utils.py                  # Core utilities (grid, SVG, image processing)
│   ├── prompts.py                # AI prompts and examples
│   └── progress_tracker.py       # Progress tracking and analytics
├── 🎭 Templates & UI
│   ├── templates/
│   │   ├── studio.html           # Main studio interface
│   │   ├── gallery.html          # Gallery management UI
│   │   ├── generate.html         # Enhanced generation form
│   │   ├── index.html            # Collaborative sketching UI
│   │   └── chat.html             # Chat-based editing UI
│   └── static/                   # Static assets and generated images
├── 📋 Configuration
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example             # Environment variables template
│   └── test_implementation.py    # Test suite
└── 📁 Output
    └── results/                  # Generated sketches and logs
        ├── enhanced/             # Enhanced generation output
        ├── batch/                # Batch generation output
        ├── test/                 # Test sketches
        └── collab_sketching/     # Collaborative sketches
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

This implementation maintains **complete feature parity** with [yael-vinker/SketchAgent](https://github.com/yael-vinker/SketchAgent) while adding these major enhancements:

### **✨ New Features Added**
- ✅ **Enhanced Generation**: 6 color palettes, 5 drawing styles, multiple variations
- ✅ **Gallery System**: Beautiful web interface to browse and manage all sketches
- ✅ **Batch Processing**: Generate multiple concepts and variations efficiently
- ✅ **Progress Tracking**: Real-time progress monitoring and task analytics
- ✅ **Studio Interface**: All-in-one web application combining all features
- ✅ **Smart Coloring**: Context-aware color selection based on concept type
- ✅ **Modern UI/UX**: Responsive design with smooth animations and gradients

### **🛠️ Technical Improvements**
- ✅ **Google Gemini API** instead of Anthropic Claude
- ✅ **Python venv** instead of Conda environment  
- ✅ **Simplified setup** with `requirements.txt`
- ✅ **Enhanced error handling** and user feedback
- ✅ **Comprehensive test suite** for validation
- ✅ **Modular architecture** with separated concerns
- ✅ **API-driven design** for better integration
- ✅ **Parallel processing** for batch operations
- ✅ **Persistent data storage** for tasks and progress

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

The enhanced system can generate sketches for various concepts with different styles and colors:

### **🎨 Style Examples**
- **Sketch Style**: Hand-drawn with natural line variations
- **Cartoon Style**: Bold, clean lines with solid colors  
- **Watercolor Style**: Soft, flowing effects with transparency
- **Minimalist Style**: Clean, simple lines with minimal detail
- **Artistic Style**: Expressive with varied stroke weights

### **🌈 Color Palette Examples**
- **Vibrant**: Bright, energetic colors (reds, blues, yellows)
- **Nature**: Earth tones and greens (forests, mountains, animals)
- **Sunset**: Warm oranges and yellows (sunsets, fire, warmth)
- **Ocean**: Blues and aquas (water, sky, cool themes)
- **Pastel**: Soft, gentle colors (flowers, dreams, calm themes)
- **Monochrome**: Classic black and white (traditional sketches)

### **📋 Concept Categories**
- 🏠 **Objects**: house, car, tree, flower, cat, dog
- 🌅 **Scenes**: landscape, cityscape, beach, forest
- 🎨 **Abstract**: emotions, concepts, ideas
- 🔄 **Interactive**: Add/modify elements via natural language
- 🎭 **Themed Collections**: Animals, nature, food, fantasy sets

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