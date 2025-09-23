#!/usr/bin/env python3
"""
Setup script for Agar crawl4ai workspace.

This script helps set up the development environment for the Agar product
catalog scraper using crawl4ai.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and handle errors."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up Agar crawl4ai workspace...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("crawl4ai/agar").exists():
        print("❌ Error: Please run this script from the crawl4ai project root directory")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Create virtual environment if it doesn't exist
    if not Path("venv").exists():
        print("\n📦 Creating virtual environment...")
        if not run_command("python3 -m venv venv"):
            print("❌ Failed to create virtual environment")
            sys.exit(1)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    print("\n📥 Installing dependencies...")
    commands = [
        "source venv/bin/activate && pip install --upgrade pip",
        "source venv/bin/activate && pip install pydantic",
        "source venv/bin/activate && pip install -e .",
        "source venv/bin/activate && python -m playwright install chromium"
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            print(f"❌ Failed to run: {cmd}")
            sys.exit(1)
    
    print("✅ Dependencies installed")
    
    # Run tests
    print("\n🧪 Running tests...")
    if not run_command("source venv/bin/activate && python -m crawl4ai.agar.test_agar"):
        print("❌ Tests failed")
        sys.exit(1)
    
    print("✅ All tests passed")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"✅ Output directory created: {output_dir}")
    
    print("\n" + "=" * 50)
    print("🎉 Workspace setup complete!")
    print("\n📚 Quick Start:")
    print("  1. Activate the virtual environment:")
    print("     source venv/bin/activate")
    print("\n  2. Run the CLI:")
    print("     python -m crawl4ai.agar.main_agar --help")
    print("\n  3. Test a single product:")
    print("     python -m crawl4ai.agar.main_agar --test-product https://agar.com.au/product/first-base/ --verbose")
    print("\n  4. Start scraping:")
    print("     python -m crawl4ai.agar.main_agar --base-url https://agar.com.au/products/ --limit 10 --verbose")
    print("\n📖 Documentation: crawl4ai/agar/README.md")
    print("🧪 Tests: python -m crawl4ai.agar.test_agar")
    print("")


if __name__ == "__main__":
    main()
