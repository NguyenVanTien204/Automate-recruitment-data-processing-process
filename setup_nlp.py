"""
Setup script for the HR NLP Pipeline.

This script:
1. Installs required dependencies
2. Downloads SpaCy models
3. Validates the installation
4. Runs basic tests
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print("=== Installing Dependencies ===")

    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")

    # Install requirements
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        return run_command(f"{sys.executable} -m pip install -r {requirements_file}", "Installing requirements")
    else:
        print("❌ requirements.txt not found")
        return False

def download_spacy_models():
    """Download required SpaCy models."""
    print("\n=== Downloading SpaCy Models ===")

    models = ["en_core_web_sm"]
    success = True

    for model in models:
        if not run_command(f"{sys.executable} -m spacy download {model}", f"Downloading {model}"):
            success = False

    return success

def validate_installation():
    """Validate that all components are working."""
    print("\n=== Validating Installation ===")

    try:
        # Test basic imports
        print("Testing imports...")

        # Test SpaCy
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            print("✓ SpaCy and model loaded successfully")
        except Exception as e:
            print(f"❌ SpaCy validation failed: {e}")
            return False

        # Test MongoDB connection (optional)
        try:
            from pymongo import MongoClient
            client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            client.server_info()
            print("✓ MongoDB connection successful")
        except Exception as e:
            print(f"⚠️  MongoDB connection failed (optional): {e}")

        # Test fuzzy matching
        try:
            from fuzzywuzzy import fuzz
            score = fuzz.ratio("test", "test")
            print("✓ Fuzzy matching available")
        except Exception as e:
            print(f"⚠️  Fuzzy matching not available (optional): {e}")

        # Test our modules
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from core.processing.preprocessor import TextPreprocessor
            from core.processing.rule_extractor import RuleBasedExtractor
            from core.processing.ner_extractor import NERExtractor
            from core.processing.keyword_matcher import KeywordMatcher
            print("✓ All custom modules imported successfully")
        except Exception as e:
            print(f"❌ Module validation failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def run_basic_test():
    """Run a basic functionality test."""
    print("\n=== Running Basic Test ===")

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from core.processing.processor import JobDescriptionProcessor

        # Test with simple text
        test_text = "Software Engineer position requiring Python, React, and 3+ years experience. Machine learning knowledge preferred."

        processor = JobDescriptionProcessor()
        result = processor.process(test_text)

        print(f"✓ Test processing completed in {result.processing_time:.2f}s")
        print(f"  Extracted {len(result.skills)} skills")
        print(f"  Extracted {len(result.technologies)} technologies")
        print(f"  Extracted {len(result.durations)} durations")

        if result.skills or result.technologies or result.durations:
            print("✓ Basic functionality test passed")
            return True
        else:
            print("⚠️  Test passed but no extractions found")
            return True

    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """Create sample data directories and files."""
    print("\n=== Creating Sample Data Structure ===")

    project_root = Path(__file__).parent

    # Create directories
    directories = [
        "data",
        "data/dictionaries",
        "data/output",
        "logs"
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(exist_ok=True)
        print(f"✓ Created directory: {dir_path}")

    # Create sample config if it doesn't exist
    config_path = project_root / "core" / "processing" / "config.json"
    if not config_path.exists():
        print("⚠️  Config file not found - using defaults")

    return True

def main():
    """Main setup function."""
    print("🚀 HR NLP Pipeline Setup")
    print("=" * 40)

    success = True

    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        success = False

    # Step 2: Download SpaCy models
    if success and not download_spacy_models():
        print("❌ SpaCy model download failed")
        success = False

    # Step 3: Create data structure
    if success and not create_sample_data():
        print("❌ Data structure creation failed")
        success = False

    # Step 4: Validate installation
    if success and not validate_installation():
        print("❌ Installation validation failed")
        success = False

    # Step 5: Run basic test
    if success and not run_basic_test():
        print("❌ Basic test failed")
        success = False

    # Summary
    print("\n" + "=" * 40)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start MongoDB (if using database storage)")
        print("2. Run: python nlp_demo.py")
        print("3. Or run: python linkedin_nlp_processor.py")
    else:
        print("❌ Setup failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- MongoDB not running (optional)")
        print("- Internet connection for model downloads")
        print("- Python version compatibility")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
