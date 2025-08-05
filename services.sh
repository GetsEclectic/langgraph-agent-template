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

# Function to show usage
show_usage() {
    echo "Usage: $0 [start|stop|restart|status]"
    echo ""
    echo "Commands:"
    echo "  start    Start both LangGraph server and Chat UI (default)"
    echo "  stop     Stop both services"
    echo "  restart  Stop and then start both services"
    echo "  status   Show status of both services"
    echo ""
    echo "Examples:"
    echo "  $0          # Start services"
    echo "  $0 start    # Start services"
    echo "  $0 stop     # Stop services"
    echo "  $0 restart  # Restart services"
    echo "  $0 status   # Check status"
}

# Function to check if a process is running
is_process_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Process is running
        else
            rm -f "$pid_file"  # Clean up stale PID file
            return 1  # Process is not running
        fi
    else
        return 1  # PID file doesn't exist
    fi
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if is_process_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        echo -e "${BLUE}🛑 Stopping $service_name (PID: $pid)...${NC}"
        kill "$pid" 2>/dev/null || true
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 "$pid" 2>/dev/null; then
                echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
                rm -f "$pid_file"
                return 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        echo -e "${YELLOW}⚠️  Force stopping $service_name...${NC}"
        kill -9 "$pid" 2>/dev/null || true
        rm -f "$pid_file"
        echo -e "${GREEN}✅ $service_name force stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  $service_name is not running${NC}"
    fi
}

# Function to show service status
show_status() {
    echo "📊 Service Status"
    echo "=================="
    
    if is_process_running "$LANGGRAPH_PID_FILE"; then
        local pid=$(cat "$LANGGRAPH_PID_FILE")
        echo -e "${GREEN}✅ LangGraph server: Running (PID: $pid, Port: $LANGGRAPH_PORT)${NC}"
    else
        echo -e "${RED}❌ LangGraph server: Not running${NC}"
    fi
    
    if is_process_running "$CHAT_UI_PID_FILE"; then
        local pid=$(cat "$CHAT_UI_PID_FILE")
        echo -e "${GREEN}✅ Chat UI: Running (PID: $pid, Port: $CHAT_UI_PORT)${NC}"
    else
        echo -e "${RED}❌ Chat UI: Not running${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🔗 Service URLs:${NC}"
    echo -e "   Chat UI:        ${YELLOW}http://localhost:$CHAT_UI_PORT${NC}"
    echo -e "   LangGraph API:  ${YELLOW}http://localhost:$LANGGRAPH_PORT${NC}"
    echo -e "   API Docs:       ${YELLOW}http://localhost:$LANGGRAPH_PORT/docs${NC}"
    echo ""
    echo -e "${BLUE}📊 Logs:${NC}"
    echo "   LangGraph: /tmp/langgraph-agent.log"
    echo "   Chat UI:   /tmp/chat-ui-agent.log"
}

# Function to stop all services
stop_services() {
    echo "🛑 Stopping LangGraph Agent Template"
    echo "====================================="
    stop_service "LangGraph server" "$LANGGRAPH_PID_FILE"
    stop_service "Chat UI" "$CHAT_UI_PID_FILE"
    echo -e "${GREEN}🎉 All services stopped!${NC}"
}

# Function to start all services
start_services() {
    echo "🚀 Starting LangGraph Agent Template"
    echo "====================================="

    # Check if services are already running
    local langgraph_running=false
    local chatui_running=false
    
    if is_process_running "$LANGGRAPH_PID_FILE"; then
        echo -e "${YELLOW}⚠️  LangGraph server is already running${NC}"
        langgraph_running=true
    fi
    
    if is_process_running "$CHAT_UI_PID_FILE"; then
        echo -e "${YELLOW}⚠️  Chat UI is already running${NC}"
        chatui_running=true
    fi
    
    if [ "$langgraph_running" = true ] && [ "$chatui_running" = true ]; then
        echo -e "${GREEN}✅ Both services are already running!${NC}"
        show_status
        return 0
    fi

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

    # Start LangGraph server if not running
    if [ "$langgraph_running" = false ]; then
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
    fi

    # Start Chat UI if not running
    if [ "$chatui_running" = false ]; then
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
    fi

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
}

# Parse command line arguments
COMMAND=${1:-start}

case $COMMAND in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        echo ""
        start_services
        ;;
    "status")
        show_status
        ;;
    "-h"|"--help"|"help")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
