def add_user_message(messages, text):
    user_message = {"role": "user", "content": text}
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)

def extract_assistant_message(message):
    for block in message.content:
        if hasattr(block, 'text'):
            return block.text
    return None