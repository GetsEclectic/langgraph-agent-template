#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default ports
LANGGRAPH_PORT=40003
CHAT_UI_PORT=40004

# PID files for cleanup
LANGGRAPH_PID_FILE="/tmp/langgraph-agent.pid"
CHAT_UI_PID_FILE="/tmp/chat-ui-agent.pid"


echo "🚀 Starting LangGraph Agent Template"
echo "====================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found.${NC}"
    echo "Please run ./setup.sh first to set up the project."
    exit 1
fi

# Check if node_modules exists in chat UI
if [ ! -d "agent-chat-ui/node_modules" ]; then
    echo -e "${RED}❌ Node.js dependencies not found in agent-chat-ui/.${NC}"
    echo "Please run ./setup.sh first to set up the project."
    exit 1
fi

# Check for environment variables
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Some features may not work.${NC}"
    echo "Create a .env file with LANGSMITH_API_KEY and ANTHROPIC_API_KEY"
fi

# Start LangGraph server
echo -e "${BLUE}🚀 Starting LangGraph server on port $LANGGRAPH_PORT...${NC}"
source venv/bin/activate
nohup python -m cli.agent serve --port $LANGGRAPH_PORT > /tmp/langgraph-agent.log 2>&1 &
LANGGRAPH_PID=$!
echo $LANGGRAPH_PID > "$LANGGRAPH_PID_FILE"

# Wait for LangGraph server to start
echo -e "${BLUE}⏳ Waiting for LangGraph server to start...${NC}"
for i in {1..30}; do
    if curl -s -o /dev/null "http://localhost:$LANGGRAPH_PORT/threads" -X POST -H "Content-Type: application/json" -d '{}'; then
        echo -e "${GREEN}✅ LangGraph server is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ LangGraph server failed to start after 30 seconds${NC}"
        echo "Check the logs at /tmp/langgraph-agent.log"
        exit 1
    fi
    sleep 1
done

# Start Chat UI
echo -e "${BLUE}🎨 Starting Chat UI on port $CHAT_UI_PORT...${NC}"
cd agent-chat-ui
nohup npm run dev -- --port $CHAT_UI_PORT > /tmp/chat-ui-agent.log 2>&1 &
CHAT_UI_PID=$!
echo $CHAT_UI_PID > "$CHAT_UI_PID_FILE"
cd ..

# Wait for Chat UI to start
echo -e "${BLUE}⏳ Waiting for Chat UI to start...${NC}"
for i in {1..30}; do
    if curl -s -o /dev/null "http://localhost:$CHAT_UI_PORT"; then
        echo -e "${GREEN}✅ Chat UI is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Chat UI failed to start after 30 seconds${NC}"
        echo "Check the logs at /tmp/chat-ui-agent.log"
        exit 1
    fi
    sleep 1
done

# Success message
echo ""
echo -e "${GREEN}🎉 All services are running!${NC}"
echo ""
echo -e "${BLUE}🔗 Access your agent:${NC}"
echo -e "   Chat UI:        ${YELLOW}http://localhost:$CHAT_UI_PORT${NC}"
echo -e "   LangGraph API:  ${YELLOW}http://localhost:$LANGGRAPH_PORT${NC}"
echo -e "   API Docs:       ${YELLOW}http://localhost:$LANGGRAPH_PORT/docs${NC}"
echo ""
echo -e "${BLUE}📊 Logs:${NC}"
echo "   LangGraph: /tmp/langgraph-agent.log"
echo "   Chat UI:   /tmp/chat-ui-agent.log"
