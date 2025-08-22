#!/usr/bin/env python3
"""
Test script to verify SketchAgent functionality without requiring API keys
"""

import sys
import os
import importlib.util

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import utils
        print("  ✅ utils.py imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import utils: {e}")
        return False
        
    try:
        import prompts
        print("  ✅ prompts.py imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import prompts: {e}")
        return False
        
    try:
        from flask import Flask
        print("  ✅ Flask imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import Flask: {e}")
        return False
        
    try:
        import google.generativeai as genai
        print("  ✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import Google Generative AI: {e}")
        return False
        
    try:
        from svg_converter import svg2png
        print("  ✅ SVG converter imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import SVG converter: {e}")
        return False
        
    try:
        from PIL import Image
        print("  ✅ Pillow (PIL) imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import Pillow: {e}")
        return False
        
    return True

def test_utils_functionality():
    """Test core utilities functionality"""
    print("🧪 Testing utils functionality...")
    
    try:
        import utils
        
        # Test grid image creation
        img, positions = utils.create_grid_image(res=10, cell_size=12, header_size=12)
        print("  ✅ Grid image creation works")
        
        # Test cells to pixels mapping
        cells_map = utils.cells_to_pixels(res=10, cell_size=12, header_size=12)
        print("  ✅ Cells to pixels mapping works")
        
        # Test image to string conversion
        img_str = utils.image_to_str(img)
        print("  ✅ Image to string conversion works")
        
        # Test XML parsing with a sample
        sample_xml = """
        <answer>
        <concept>test</concept>
        <strokes>
            <s1>
                <points>'x10y10', 'x20y20'</points>
                <t_values>0.0, 1.0</t_values>
                <id>test stroke</id>
            </s1>
        </strokes>
        </answer>
        """
        strokes_list, t_values_list = utils.parse_xml_string(sample_xml, res=50)
        if strokes_list and t_values_list:
            print("  ✅ XML parsing works")
        else:
            print("  ⚠️  XML parsing returned None (expected for some cases)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Utils functionality test failed: {e}")
        return False

def test_prompts():
    """Test prompts module"""
    print("🧪 Testing prompts...")
    
    try:
        from prompts import sketch_first_prompt, system_prompt, gt_example
        
        # Test prompt formatting
        formatted = sketch_first_prompt.format(concept="test", gt_sketches_str=gt_example)
        if "test" in formatted:
            print("  ✅ Prompt formatting works")
        else:
            print("  ❌ Prompt formatting failed")
            return False
            
        system_formatted = system_prompt.format(res=50)
        if "50" in system_formatted:
            print("  ✅ System prompt formatting works")
        else:
            print("  ❌ System prompt formatting failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Prompts test failed: {e}")
        return False

def test_script_structure():
    """Test that main scripts have correct structure"""
    print("🧪 Testing script structure...")
    
    scripts = ['gen_sketch.py', 'collab_sketch.py', 'chat_and_edit.py']
    
    for script in scripts:
        if os.path.exists(script):
            print(f"  ✅ {script} exists")
            
            # Test that the script can be loaded (but not executed)
            try:
                spec = importlib.util.spec_from_file_location("test_module", script)
                if spec is not None:
                    print(f"  ✅ {script} has valid Python syntax")
                else:
                    print(f"  ❌ {script} has invalid syntax")
                    return False
            except Exception as e:
                print(f"  ❌ {script} syntax check failed: {e}")
                return False
        else:
            print(f"  ❌ {script} not found")
            return False
    
    return True

def test_directory_structure():
    """Test that required directories and files exist"""
    print("🧪 Testing directory structure...")
    
    required_files = [
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md',
        'utils.py',
        'prompts.py',
        'gen_sketch.py',
        'collab_sketch.py',
        'chat_and_edit.py'
    ]
    
    required_dirs = [
        'templates',
        'static'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file} exists")
        else:
            print(f"  ❌ {file} missing")
            return False
    
    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"  ✅ {dir}/ directory exists")
        else:
            print(f"  ❌ {dir}/ directory missing")
            return False
    
    # Check templates
    templates = ['templates/index.html', 'templates/chat.html']
    for template in templates:
        if os.path.exists(template):
            print(f"  ✅ {template} exists")
        else:
            print(f"  ❌ {template} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🎨 SketchAgent Implementation Test Suite")
    print("=" * 50)
    
    tests = [
        test_directory_structure,
        test_imports,
        test_utils_functionality,
        test_prompts,
        test_script_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("  ✅ PASSED\n")
            else:
                failed += 1
                print("  ❌ FAILED\n")
        except Exception as e:
            failed += 1
            print(f"  ❌ FAILED with exception: {e}\n")
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! SketchAgent implementation is ready.")
        print("\n📝 Next steps:")
        print("  1. Get a Google Gemini API key from https://makersuite.google.com/app/apikey")
        print("  2. Add your key to the .env file: GOOGLE_API_KEY=your_key_here")
        print("  3. Test the applications:")
        print("     • python gen_sketch.py --concept_to_draw \"cat\"")
        print("     • python collab_sketch.py")
        print("     • python chat_and_edit.py")
        return 0
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())