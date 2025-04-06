"""
Main entry point for the GPTTransit application.
"""

import argparse
from llm.agent import AgentManager
from ui.gradio_interface import ChatInterface


def main():
    """
    Main function to run the GPTTransit application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GPTTransit Chatbot Application")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--server-name", default="localhost", help="Server name to listen on")   # 0.0.0.0
    parser.add_argument("--server-port", type=int, default=7860, help="Port to run the server on")
    args = parser.parse_args()
    
    # Initialize the agent manager
    agent_manager = AgentManager()
    
    # Initialize the chat interface
    chat_interface = ChatInterface(agent_manager)
    
    # Launch the interface
    print("Launching GPTTransit chatbot...")
    chat_interface.launch(
        share=args.share,
        server_name=args.server_name,
        server_port=args.server_port
    )


if __name__ == "__main__":
    main()