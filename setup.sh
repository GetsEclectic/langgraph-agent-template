#!/bin/bash
set -e

echo "🚀 Setting up LangGraph Agent Template"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is required but not installed.${NC}"
    echo "Please install Node.js 18+ and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is required but not installed.${NC}"
    echo "Please install npm and try again."
    exit 1
fi

echo -e "${BLUE}🔍 Checking Python version...${NC}"
python_version=$(python3 --version | cut -d' ' -f2)
echo "Found Python $python_version"

echo -e "${BLUE}🔍 Checking Node.js version...${NC}"
node_version=$(node --version)
echo "Found Node.js $node_version"

# Create Python virtual environment
echo -e "${BLUE}🐍 Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists, skipping...${NC}"
fi

# Activate virtual environment and install dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Install Node.js dependencies for chat UI
echo -e "${BLUE}📦 Installing Node.js dependencies for chat UI...${NC}"
cd agent-chat-ui
npm install
cd ..
echo -e "${GREEN}✅ Node.js dependencies installed${NC}"

# Setup environment variables
echo -e "${BLUE}🔑 Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file from .env.example${NC}"
        echo -e "${YELLOW}📝 Please edit .env and fill in your API keys:${NC}"
        echo "   - ANTHROPIC_API_KEY: Get from https://console.anthropic.com"
        echo "   - LANGSMITH_API_KEY: Get from https://smith.langchain.com"
        echo ""
        echo -e "${YELLOW}💡 The services won't work until you add your API keys to .env${NC}"
    else
        echo -e "${RED}❌ No .env.example file found${NC}"
        echo "Please create a .env file with your API keys"
    fi
else
    echo -e "${GREEN}✅ Found existing .env file${NC}"
    # Check if it contains placeholder values
    if grep -q "your_.*_api_key_here" .env; then
        echo -e "${YELLOW}⚠️  .env file contains placeholder values${NC}"
        echo -e "${YELLOW}📝 Please edit .env and fill in your actual API keys${NC}"
    fi
fi

# Success message
echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Set up your environment variables in .env file:"
echo "   - LANGSMITH_API_KEY=your_key_here"
echo "   - ANTHROPIC_API_KEY=your_key_here"
echo ""
echo "2. Run the services with:"
echo -e "   ${YELLOW}./start.sh${NC}"
echo ""
echo "3. Access the chat UI at:"
echo -e "   ${BLUE}http://localhost:40004${NC}"