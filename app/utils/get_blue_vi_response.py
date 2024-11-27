from typing import List, Tuple, Optional
import logging
from llama_cpp import Llama, llama_grammar
from starlette.concurrency import run_in_threadpool
from app.types.enum.gpt import Role


def trim_messages(messages: List[dict], max_tokens: int = 512) -> List[dict]:
    """
    Trim messages to ensure the total token count does not exceed the max_tokens.

    Args:
    - messages (List[dict]): List of formatted message dictionaries.
    - max_tokens (int): Maximum number of tokens allowed.

    Returns:
    - List[dict]: Trimmed list of message dictionaries.
    """
    total_tokens = sum(
        len(message['content'].split())
        for message in messages
        if isinstance(message, dict)
    )
    while total_tokens > max_tokens and messages:
        # Remove the first message until we are within the token limit
        removed_message = messages.pop(0)
        total_tokens -= (
            len(removed_message['content'].split())
            if isinstance(removed_message, dict)
            else 0
        )

    return messages


def get_operation_format(
    conversation_history: List[Tuple[str, str]]
) -> List[dict]:
    """
    Format the conversation history into the structure expected by the Llama model.

    Args:
    - conversation_history (List[Tuple[str, str]]): List of tuples (role, message).

    Returns:
    - List[dict]: Formatted list of messages.
    """
    formatted_messages = []

    for conversation in conversation_history:
        if (
            len(conversation) != 2
            or not isinstance(conversation[0], str)
            or not isinstance(conversation[1], str)
        ):
            logging.error(f"Invalid tuple: {conversation}")
            continue  # Skip invalid tuples

        role, message = conversation
        if role in {Role.USER.value, Role.ASSISTANT.value, Role.SYSTEM.value}:
            message_dict = {'role': role, 'content': message}
            if isinstance(message_dict, dict):
                formatted_messages.append(message_dict)
            else:
                logging.error(
                    f"Formatted message is not a dict: {message_dict}"
                )
        else:
            logging.warning(
                f"Unrecognized role '{role}' in conversation: {conversation}"
            )

    return formatted_messages


async def get_blue_vi_response(
    llm: Llama,
    conversation_history: List[Tuple[str, str]],
    grammar: Optional[llama_grammar] = None,
) -> dict:
    """
    Get the model's response to the conversation history.

    Args:
    - llm (Llama): The Llama model instance.
    - conversation_history (List[Tuple[str, str]]): History of the conversation as (role, message) tuples.
    - grammar (Optional[llama_grammar]): Optional grammar for the model.

    Returns:
    - dict: The model's response.
    """
    try:
        # Format the conversation history
        messages = get_operation_format(conversation_history)
        logging.info(f"Formatted messages: {messages}")

        # Trim messages to not exceed the max token limit
        messages = trim_messages(messages)
        logging.info(f"Trimmed messages: {messages}")

        # Ensure the formatted messages meet the model's requirements
        if not messages:
            logging.error("No valid messages to process")
            return {}

        # Generate response using Llama in a thread pool
        logging.info("Generating response with Llama")
        response = await run_in_threadpool(
            lambda: llm.create_chat_completion(
                messages=messages, grammar=grammar
            )
        )
        logging.info(f"Model response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error communicating with the model: {e}")
        return {}
