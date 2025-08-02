#!/usr/bin/env python3
"""
🚀 Pokemon Card Automation Agent - Quick Setup Script
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print setup banner"""
    print("\n" + "="*60)
    print("🤖 Pokemon Card Automation Agent - Quick Setup")
    print("="*60)


def check_python_version():
    """Ensure Python 3.10+"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def setup_environment():
    """Create .env file from template"""
    env_file = Path(".env")
    template_file = Path(".env.template")
    
    if not env_file.exists() and template_file.exists():
        shutil.copy(template_file, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env with your credentials")
    else:
        print("✅ .env file already exists")


def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False
    return True


def install_playwright():
    """Install Playwright browsers"""
    print("🎭 Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True)
        print("✅ Playwright browsers installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Playwright browsers")
        return False
    return True


def create_directories():
    """Create necessary directories"""
    dirs = ["logs", "browser-profiles", "auth_configs", "retailer_configs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Created necessary directories")


def main():
    """Main setup function"""
    print_banner()
    
    check_python_version()
    create_directories()
    setup_environment()
    
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        return
        
    if not install_playwright():
        print("❌ Setup failed during browser installation")
        return
    
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("1. Edit .env with your AgentQL API key and credentials")
    print("2. Configure retailer_configs/bestbuy.json with SKUs to monitor")
    print("3. Run: python -m src.main")
    print("\n🚀 Quick start guide: 🚀_START_HERE.md")
    print("📚 Full documentation: README.md")
    print("\nMay your pulls be legendary! ✨")


if __name__ == "__main__":
    main()