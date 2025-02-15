import re
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# Initialize the base LLM model
llm = init_chat_model("llama3-8b-8192", model_provider="groq")

# ============================
# Administrative Agent System Message
# ============================
administrative_system = SystemMessage(
    content=(
        "You are the Administrative Agent. You have access to external APIs such as calendar, texts, and todo lists. "
        "If needed, output a function call using the format:\n"
        "CALL: function_name(arg1, arg2, ...)\n"
        "For example, to schedule a meeting, you might output:\n"
        'CALL: schedule_meeting("2025-03-01", "10:00 AM")\n'
        "If a function needs to be called inside another (e.g., to get tomorrow's date), use nested calls. "
        "For instance:\n"
        'CALL: schedule_meeting(CALL: get_tomorrow\'s_date(), "10:00 AM")\n'
        "Otherwise, simply provide a helpful answer."
    )
)

# ============================
# Simulated Functions (APIs)
# ============================
def get_tomorrow_date() -> str:
    """
    Simulate retrieving tomorrow's date.
    In a real implementation, this would calculate or query the date.
    """
    return "2025-03-01"

def schedule_meeting(date: str, time: str) -> str:
    """
    Simulate scheduling a meeting.
    In a real implementation, this function would integrate with a calendar API.
    """
    return f"Meeting successfully scheduled for {date} at {time}."

# ============================
# Parsing and Dispatch Helpers
# ============================
def parse_call(call_str: str):
    """
    Parse a function call string in the format:
    function_name(arg1, arg2, ...)
    Supports one level (or nested) function calls.
    Returns a tuple: (function_name, [arg1, arg2, ...])
    """
    # If the string starts with "CALL:", remove it.
    if call_str.startswith("CALL:"):
        call_str = call_str[len("CALL:"):].strip()
    
    # Match function name and inner arguments
    m = re.match(r"([\w']+)\((.*)\)", call_str)
    if not m:
        return None, []
    func_name = m.group(1)
    args_str = m.group(2)
    
    # Split arguments on commas that are not inside parentheses.
    args = []
    current = ""
    paren_level = 0
    for char in args_str:
        if char == "(":
            paren_level += 1
        elif char == ")":
            paren_level -= 1
        if char == "," and paren_level == 0:
            args.append(current.strip())
            current = ""
        else:
            current += char
    if current:
        args.append(current.strip())
    
    evaluated_args = []
    for arg in args:
        # If the argument starts with "CALL:", it's a nested call.
        if arg.startswith("CALL:"):
            # Recursively process the nested call.
            inner_call = arg[len("CALL:"):].strip()
            inner_func, inner_args = parse_call(inner_call)
            if inner_func and inner_func.replace("'", "") == "get_tomorrow_date":
                evaluated_args.append(get_tomorrow_date())
            else:
                evaluated_args.append(arg)  # Fallback: leave as string.
        # If the argument is enclosed in quotes, remove them.
        elif (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
            evaluated_args.append(arg[1:-1])
        # Otherwise, keep as is.
        else:
            evaluated_args.append(arg)
    return func_name, evaluated_args

def process_admin_response(response: str) -> str:
    """
    Process the Administrative Agent's response.
    If function calls are present, extract and execute the final call.
    """
    # Find all function calls in the response using a simple regex.
    pattern = r'CALL:\s*(.+)'
    matches = re.findall(pattern, response)
    
    if matches:
        # Process the last function call in the response.
        final_call_str = matches[-1].strip()
        func_name, args = parse_call(final_call_str)
        # Dispatch the function call.
        if func_name and func_name.replace("'", "") == "schedule_meeting":
            try:
                result = schedule_meeting(*args)
                return result
            except TypeError as te:
                return f"Error in function arguments: {te}"
        else:
            return f"Unknown function: {func_name}"
    else:
        # No function call detected; return the original response.
        return response

# ============================
# LLM Invocation Helper
# ============================
def invoke_agent(system_message: SystemMessage, user_prompt: str) -> str:
    """Helper function to invoke an agent with a system and user message."""
    messages = [
        system_message,
        HumanMessage(content=user_prompt)
    ]
    response = llm.invoke(messages)
    return response.content.strip()

# ============================
# Administrative Agent Handler
# ============================
def administrative_agent_handle(user_request: str) -> str:
    """
    Handle the request using the Administrative Agent.
    The agent's response may include one or more function calls.
    We process the final function call in the response.
    """
    response = invoke_agent(administrative_system, user_request)
    print("Raw response from Administrative Agent:")
    print(response)
    
    processed_response = process_admin_response(response)
    return processed_response

# ============================
# Example Usage
# ============================
if __name__ == "__main__":
    # Example user request that might require scheduling a meeting.
    user_request = "Can you schedule a meeting for tomorrow at 10 AM?"
    
    final_output = administrative_agent_handle(user_request)
    
    print("\nFinal Output:")
    print(final_output)
