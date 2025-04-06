"""
Agent configuration and execution.
"""

from langchain.agents import load_tools, create_openai_tools_agent, AgentExecutor

from llm.models import init_openai_chat_model
from llm.prompts import get_chat_prompt_template
from llm.memory import ConversationMemoryManager

from tools.transport_tools import get_public_transport_route_concise, checkTrainAlert
from tools.location_tools import getGPS, checkNearestTaxiStands, checkNearestAttractions
from tools.crowd_tools import checkRealTimeCrowd, checkForecastVolume
from tools.weather_tools import get_2h_24h_weather_forecast


class AgentManager:
    """
    Manages the creation and execution of the LangChain agent.
    """
    
    def __init__(self):
        """Initialize the agent manager."""
        self.llm = init_openai_chat_model()
        self.tools = self._init_tools()
        self.prompt = get_chat_prompt_template()
        self.memory_manager = ConversationMemoryManager()
        self.agent = self._create_agent()
        self.agent_executor = self._create_agent_executor()
        self.agent_chain = self.memory_manager.get_memory_chain(self.agent_executor)
    
    def _init_tools(self):
        """
        Initialize all the tools for the agent.
        
        Returns:
            list: List of tools
        """
        # Load built-in calculator tool
        math_tools = load_tools(["llm-math"], llm=self.llm)
        
        # Custom tools
        custom_tools = [
            get_public_transport_route_concise,
            getGPS,
            get_2h_24h_weather_forecast,
            # checkTrainAlert,
            checkNearestTaxiStands,
            checkForecastVolume,
            checkRealTimeCrowd,
            checkNearestAttractions
        ]
        
        # Combine all tools
        return math_tools + custom_tools
    
    def _create_agent(self):
        """
        Create the OpenAI tools agent.
        
        Returns:
            Agent: The configured agent
        """
        return create_openai_tools_agent(self.llm, self.tools, self.prompt)
    
    def _create_agent_executor(self):
        """
        Create the agent executor.
        
        Returns:
            AgentExecutor: The agent executor
        """
        return AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def invoke(self, input_message, session_id="default"):
        """
        Invoke the agent with a user message.
        
        Args:
            input_message (str): The user's input message
            session_id (str): Session identifier for memory management
            
        Returns:
            dict: The agent's response
        """
        return self.agent_chain.invoke(
            {"input": input_message},
            {"configurable": {"session_id": session_id}}
        )
    
    def clear_memory(self):
        """Clear the conversation memory."""
        self.memory_manager.clear_memory()