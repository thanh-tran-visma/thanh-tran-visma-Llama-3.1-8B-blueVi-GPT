import logging
from llama_cpp import Llama, ChatCompletionRequestUserMessage
from huggingface_hub import login
from app.config.config_env import MODEL_NAME, HF_TOKEN, GGUF_MODEL
from app.types.llm_types import Message, Response
from typing import List


class BlueViGptModel:
    def __init__(self):
        self.llm = self.load_model()

    @staticmethod
    def load_model():
        model_cache_dir = "./model_cache"
        if HF_TOKEN:
            login(HF_TOKEN)
        else:
            raise ValueError("HF_TOKEN environment variable is not set.")

        llm = Llama.from_pretrained(
            repo_id=MODEL_NAME,
            filename=GGUF_MODEL,
            cache_dir=model_cache_dir,
        )
        return llm

    def get_response(self, conversation_history: List[Message]) -> Response:
        try:
            # Create messages in the required format
            mapped_messages: List[ChatCompletionRequestUserMessage] = [
                ChatCompletionRequestUserMessage(
                    role="user", content=msg.content
                )  # Use "user" as a literal
                for msg in conversation_history
            ]

            response = self.llm.create_chat_completion(
                messages=mapped_messages
            )

            choices = response.get("choices")
            if isinstance(choices, list) and len(choices) > 0:
                message_content = choices[0]["message"]["content"]
                return Response(content=message_content)

            else:
                return Response("Sorry, I couldn't generate a response.")

        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return Response(
                "Sorry, an error occurred while generating a response."
            )

    def get_anonymized_message(self, user_message: str) -> Response:
        instruction = f"Anonymize the data:\n{user_message}\n"

        try:
            response = self.llm.create_chat_completion(
                messages=[
                    ChatCompletionRequestUserMessage(
                        role="user", content=instruction
                    )
                ]  # Use "user" as a literal
            )
            choices = response.get("choices")
            if isinstance(choices, list) and len(choices) > 0:
                message_content = choices[0]["message"]["content"]
                return Response(content=message_content)
            else:
                return Response(
                    "Sorry, I couldn't generate an anonymized response.",
                    0,
                    0,
                )

        except Exception as e:
            logging.error(f"Error generating anonymized message: {e}")
            return Response(
                "Sorry, an error occurred while generating an anonymized response.",
                0,
                0,
            )
