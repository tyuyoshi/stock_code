#!/bin/bash

# Stock Code Setup Script
# This script sets up the development environment for the Stock Code project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Stock Code Development Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check for required tools
echo -e "${YELLOW}Checking required tools...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.11 or higher.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found: $(docker --version)${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}  Please edit .env file with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""

# Backend setup
echo -e "${YELLOW}Setting up Backend...${NC}"
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

cd ..
echo ""

# Frontend setup
echo -e "${YELLOW}Setting up Frontend...${NC}"
cd frontend

# Install npm dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install --silent
    echo -e "${GREEN}✓ npm dependencies installed${NC}"
else
    echo -e "${GREEN}✓ npm dependencies already installed${NC}"
fi

cd ..
echo ""

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data
echo -e "${GREEN}✓ Directories created${NC}"

echo ""

# Docker setup
echo -e "${YELLOW}Docker Setup...${NC}"
echo "Building Docker images..."

if docker-compose build --quiet; then
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
else
    echo -e "${YELLOW}⚠ Docker build failed. You can build manually with: docker-compose build${NC}"
fi

echo ""

# Final instructions
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your configuration"
echo "2. Start the services:"
echo "   - With Docker: docker-compose up"
echo "   - Without Docker:"
echo "     - Backend: cd backend && source venv/bin/activate && uvicorn api.main:app --reload"
echo "     - Frontend: cd frontend && npm run dev"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/api/docs"
echo "   - pgAdmin (optional): http://localhost:5050"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"