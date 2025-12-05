#!/bin/bash

echo "🎃 Testing MCP Servers for Watcher 🎃"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Check if Python packages are installed
echo "1. Checking Python dependencies..."
if python3 -c "import mcp" 2>/dev/null; then
    echo -e "${GREEN}✓ mcp package installed${NC}"
else
    echo -e "${RED}✗ mcp package missing${NC}"
    echo "  Installing: pip3 install mcp"
    pip3 install mcp --quiet
fi

if python3 -c "import google.generativeai" 2>/dev/null; then
    echo -e "${GREEN}✓ google-generativeai package installed${NC}"
else
    echo -e "${RED}✗ google-generativeai package missing${NC}"
    echo "  Installing: pip3 install google-generativeai"
    pip3 install google-generativeai --quiet
fi

if python3 -c "import psycopg2" 2>/dev/null; then
    echo -e "${GREEN}✓ psycopg2 package installed${NC}"
else
    echo -e "${RED}✗ psycopg2 package missing${NC}"
    echo "  Installing: pip3 install psycopg2-binary"
    pip3 install psycopg2-binary --quiet
fi

echo ""

# Test 2: Check if MCP servers exist
echo "2. Checking MCP server files..."
if [ -f ".kiro/mcp-servers/watcher-api-server.py" ]; then
    echo -e "${GREEN}✓ Watcher API server exists${NC}"
else
    echo -e "${RED}✗ Watcher API server missing${NC}"
fi

if [ -f ".kiro/mcp-servers/kiroween-scoring.py" ]; then
    echo -e "${GREEN}✓ Kiroween scoring server exists${NC}"
else
    echo -e "${RED}✗ Kiroween scoring server missing${NC}"
fi

if [ -f ".kiro/mcp-servers/gemini-test-server.py" ]; then
    echo -e "${GREEN}✓ Gemini test server exists${NC}"
else
    echo -e "${RED}✗ Gemini test server missing${NC}"
fi

echo ""

# Test 3: Check if config exists
echo "3. Checking MCP configuration..."
if [ -f ".kiro/settings/mcp.json" ]; then
    echo -e "${GREEN}✓ Workspace MCP config exists${NC}"
    echo "  Servers configured:"
    cat .kiro/settings/mcp.json | grep -o '"[^"]*":' | grep -v "mcpServers\|command\|args\|env\|disabled\|autoApprove" | sed 's/://g' | sed 's/"//g' | sed 's/^/    - /'
else
    echo -e "${RED}✗ Workspace MCP config missing${NC}"
fi

echo ""

# Test 4: Check if Docker is running
echo "4. Checking Docker services..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Docker services are running${NC}"
    docker-compose ps | grep "Up" | awk '{print "    - " $1}'
else
    echo -e "${YELLOW}⚠ Docker services not running${NC}"
    echo "  Start with: docker-compose up -d"
fi

echo ""

# Test 5: Check environment variables
echo "5. Checking environment variables..."
if [ -n "$GEMINI_API_KEY" ] || [ -n "$LLM_API_KEY" ]; then
    echo -e "${GREEN}✓ Gemini API key is set${NC}"
else
    echo -e "${YELLOW}⚠ Gemini API key not set${NC}"
    echo "  Set with: export GEMINI_API_KEY='your-key'"
    echo "  Get key at: https://aistudio.google.com/app/apikey"
fi

if [ -n "$GITHUB_TOKEN" ]; then
    echo -e "${GREEN}✓ GitHub token is set${NC}"
else
    echo -e "${YELLOW}⚠ GitHub token not set${NC}"
    echo "  Set with: export GITHUB_TOKEN='your-token'"
    echo "  Get token at: https://github.com/settings/tokens"
fi

echo ""

# Test 6: Test database connection
echo "6. Testing database connection..."
if docker-compose exec -T db psql -U postgres -d watcher -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "  Make sure Docker is running: docker-compose up -d"
fi

echo ""
echo "========================================="
echo "Setup Status:"
echo ""

# Count successes
SUCCESS=0
TOTAL=6

[ -f ".kiro/mcp-servers/watcher-api-server.py" ] && ((SUCCESS++))
[ -f ".kiro/settings/mcp.json" ] && ((SUCCESS++))
python3 -c "import mcp" 2>/dev/null && ((SUCCESS++))
python3 -c "import google.generativeai" 2>/dev/null && ((SUCCESS++))
python3 -c "import psycopg2" 2>/dev/null && ((SUCCESS++))
docker-compose ps | grep -q "Up" && ((SUCCESS++))

if [ $SUCCESS -eq $TOTAL ]; then
    echo -e "${GREEN}✓ All checks passed! ($SUCCESS/$TOTAL)${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Restart Kiro to load MCP servers"
    echo "2. Try: 'Get database stats' in Kiro chat"
    echo "3. Try: 'Calculate score for haunt_created'"
    echo "4. Try: 'Test my Gemini API key'"
else
    echo -e "${YELLOW}⚠ Some checks failed ($SUCCESS/$TOTAL)${NC}"
    echo ""
    echo "Review the errors above and:"
    echo "1. Install missing packages"
    echo "2. Start Docker services"
    echo "3. Set environment variables"
    echo "4. Restart Kiro"
fi

echo ""
echo "📚 See MCP_SETUP_GUIDE.md for detailed instructions"
echo "========================================="
