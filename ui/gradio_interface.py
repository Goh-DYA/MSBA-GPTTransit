"""
Gradio web interface for the GPTTransit chatbot.
"""

import os
import gradio as gr
from typing import List, Tuple, Optional


class ChatInterface:
    """
    Manages the Gradio web interface for the chatbot.
    """
    
    def __init__(self, agent_manager):
        """
        Initialize the chat interface.
        
        Args:
            agent_manager: The agent manager for handling chat interactions
        """
        self.agent_manager = agent_manager
        self.welcome_message = (
            "🚇 Welcome to GPTTransit! 🚶‍♂️\n\n"
            "I'm here to help you navigate MRT trains, find walking routes and locate taxi "
            "stands effortlessly. Whether you're planning your journey or exploring options, "
            "I've got you covered! Let's make commuting a breeze together!"
        )
        
        # Get paths for avatar images
        current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.user_avatar = os.path.join(current_directory, "assets", "user.png")
        self.bot_avatar = os.path.join(current_directory, "assets", "LTA_logo.jpg")
    
    def _print_like_dislike(self, x: gr.LikeData):
        """
        Handle like/dislike feedback.
        
        Args:
            x: Like data from Gradio
        """
        print(f"Message {x.index} {'liked' if x.liked else 'disliked'}: {x.value}")
    
    def _add_text(self, history: List[Tuple[str, Optional[str]]], text: str) -> Tuple[List[Tuple[str, Optional[str]]], gr.Textbox]:
        """
        Add user text to chat history.
        
        Args:
            history: Current chat history
            text: User's input text
            
        Returns:
            tuple: Updated history and textbox
        """
        history = history + [(text, None)]
        return history, gr.Textbox(value="", interactive=False)
    
    def _bot_response(self, history: List[Tuple[str, Optional[str]]]) -> List[Tuple[str, str]]:
        """
        Generate bot response for the user's query.
        
        Args:
            history: Current chat history
            
        Returns:
            list: Updated chat history with bot response
        """
        # Get the last message from the user
        query = history[-1][0]
        
        try:
            # Call the agent manager to get a response
            response = self.agent_manager.invoke(query)
            response_text = response['output']
            
            # Update history with the response
            history[-1] = (query, response_text)
            yield history
        except Exception as e:
            # Handle errors
            error_message = f"I encountered an error: {str(e)}\nPlease try again or rephrase your question."
            history[-1] = (query, error_message)
            yield history
    
    def create_interface(self):
        """
        Create and configure the Gradio interface.
        
        Returns:
            gr.Blocks: Configured Gradio interface
        """
        with gr.Blocks() as demo:
            chatbot = gr.Chatbot(
                value=[[None, self.welcome_message]],
                elem_id="chatbot",
                bubble_full_width=False,
                avatar_images=(self.user_avatar, self.bot_avatar),
                height=600,
                scale=1
            )

            with gr.Row():
                txt = gr.Textbox(
                    scale=5,
                    show_label=False,
                    placeholder="Enter text and press enter",
                    container=False,
                )
                clear = gr.Button("Clear")

            txt_msg = txt.submit(
                self._add_text, [chatbot, txt], [chatbot, txt], queue=False
            ).then(
                self._bot_response, chatbot, chatbot, api_name="bot_response"
            )
            
            txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)

            chatbot.like(self._print_like_dislike, None, None)
            clear.click(lambda: None, None, chatbot, queue=False)

        return demo
    
    def launch(self, share=False, server_name="0.0.0.0", server_port=7860):
        """
        Launch the Gradio interface.
        
        Args:
            share (bool): Whether to create a shareable link
            server_name (str): Server name to listen on
            server_port (int): Port to run the server on
        """
        demo = self.create_interface()
        demo.queue()
        demo.launch(share=share, server_name=server_name, server_port=server_port)