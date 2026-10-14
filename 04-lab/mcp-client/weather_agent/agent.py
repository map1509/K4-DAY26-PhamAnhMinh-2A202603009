"""
Weather Agent - Connects to Remote MCP Server on Cloud Run
Successfully connects to custom MCP HTTP endpoints!
"""
from google.adk import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

weather_model = Gemini(
    model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
    retry_options=types.HttpRetryOptions(
        attempts=5,
        initial_delay=2,
        max_delay=16,
        exp_base=2,
        jitter=1,
        http_status_codes=[500, 502, 503, 504],
    ),
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mặc định: server chạy local. Deploy lên Cloud Run thì đặt MCP_SERVER_URL trong .env
# (ví dụ: https://<service>.run.app/mcp). verify_setup.py đọc cùng biến này.
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

logger.info(f"🌐 Initializing weather agent with remote MCP server")
logger.info(f"📡 MCP Server: {MCP_SERVER_URL}")

try:
    # Create connection parameters for the remote MCP server
    connection_params = StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,  # Increased timeout for Cloud Run cold starts
    )
    
    # Create the MCP toolset - this will connect to the remote server
    logger.info("🔌 Connecting to MCP server...")
    weather_tools = McpToolset(
        connection_params=connection_params,
    )
    logger.info("✅ MCP toolset created successfully")
    
    # Create the agent with remote MCP tools
    root_agent = Agent(
        name="weather_agent",
        model=weather_model,
        generate_content_config=types.GenerateContentConfig(
            max_output_tokens=2048,
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
            http_options=types.HttpOptions(timeout=60_000),
        ),
        instruction=(
            "Trả lời bằng tiếng Việt. Luôn gọi MCP tool để lấy dữ liệu thời tiết thật; "
            "không tự suy đoán số liệu. Với thời tiết hiện tại, nêu nhiệt độ, cảm giác như, "
            "độ ẩm, gió, UV và thời điểm cập nhật. Với dự báo, nêu ngày, nhiệt độ cao/thấp "
            "và khả năng mưa cho tối đa 3 ngày."
        ),
        tools=[weather_tools],
    )
    logger.info("✅ Weather agent initialized with remote MCP tools:")
    logger.info("   - get_current_weather(city)")
    logger.info("   - get_forecast(city, days)")
    logger.info("   - health_check()")
    logger.info("🎉 Remote MCP connection successful!")
    
except Exception as e:
    logger.error(f"❌ Failed to connect to remote MCP server: {e}")
    logger.error(f"   Server URL: {MCP_SERVER_URL}")
    import traceback
    traceback.print_exc()
    
    # Create a fallback agent without tools
    logger.warning("⚠️  Creating fallback agent without MCP tools")
    root_agent = Agent(
        name="weather_agent",
        model=weather_model,
    )

