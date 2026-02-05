#!/bin/bash

echo "================================================"
echo "NTU Travel Management System - Startup Script"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if MongoDB is running
echo -e "${YELLOW}Checking MongoDB connection...${NC}"
if mongosh --eval "db.runCommand({ ping: 1 })" mongodb://localhost:27017/ntu_travel > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MongoDB is running and accessible${NC}"
else
    echo -e "${RED}✗ MongoDB is not running or not accessible${NC}"
    echo -e "${YELLOW}Please start MongoDB first:${NC}"
    echo "  - Windows: Start MongoDB service from Services"
    echo "  - Linux/Mac: sudo systemctl start mongod"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r app/requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Starting NTU Travel Management System...${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}API Documentation will be available at:${NC}"
echo "  → http://localhost:8000/docs"
echo "  → http://localhost:8000/redoc"
echo ""
echo -e "${YELLOW}Health Check:${NC}"
echo "  → http://localhost:8000/health"
echo ""

# Start the application
cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000
