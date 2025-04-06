"""
Memory management for the conversational agent.
"""

from langchain.memory import ChatMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory

from llm.models import init_huggingface_model
from llm.prompts import get_summarization_prompt


class ConversationMemoryManager:
    """
    Manages the conversation memory and summarization for the agent.
    """
    
    def __init__(self):
        """Initialize the conversation memory manager."""
        self.chat_memory = ChatMessageHistory()
        self.summarization_llm = init_huggingface_model()
        self.summarization_prompt = get_summarization_prompt()
    
    def get_memory_chain(self, agent_executor):
        """
        Create a chain that includes memory management.
        
        Args:
            agent_executor: The agent executor to wrap with memory
            
        Returns:
            chain: A chain with memory management
        """
        # Create a memory-enabled agent
        conversational_agent_executor = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: self.chat_memory,
            input_messages_key="input",
            output_messages_key="output",
            history_messages_key="chat_history",
        )
        
        # Create a chain that includes summarization
        chain_with_summarization = (
            RunnablePassthrough.assign(messages_summarized=self.summarize_messages)
            | conversational_agent_executor
        )
        
        return chain_with_summarization
    
    def summarize_messages(self, chain_input):
        """
        Summarize the conversation history.
        
        Args:
            chain_input: The input to the chain
            
        Returns:
            bool: True if messages were summarized, False otherwise
        """
        stored_messages = self.chat_memory.messages
        
        if len(stored_messages) == 0:
            return False
        
        # Create summarization chain
        summarization_chain = self.summarization_prompt | self.summarization_llm
        
        # Generate summary
        summary_message = summarization_chain.invoke({"chat_history": stored_messages})
        
        # Replace chat history with summary
        self.chat_memory.clear()
        self.chat_memory.add_message(summary_message)
        
        return True
    
    def clear_memory(self):
        """Clear the conversation memory."""
        self.chat_memory.clear()
        
    def get_memory(self):
        """
        Get the current conversation memory.
        
        Returns:
            list: The conversation messages
        """
        return self.chat_memory.messages