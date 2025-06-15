import logging
import json
import os
from pathlib import Path
from autogen import AssistantAgent
from src.config.settings import LLM_CONFIG
from src.tools.file_read_tool import read_file
from src.tools.file_write_tool import write_file

logger = logging.getLogger(__name__)

def process_story_to_code(state: dict) -> str:
    """Generate code based on stories and update state dict."""
    try:
        # Define directories
        project_root = str(Path(__file__).parent.parent.parent)
        stories_dir = os.path.join(project_root, "stories")
        programs_dir = os.path.join(project_root, "programs")
        os.makedirs(programs_dir, exist_ok=True)

        stories_file = state.get("stories_file")
        if not stories_file:
            raise ValueError("No stories file found in state. Ensure BA agent has generated stories.")

        # Load story content
        stories_path = os.path.join(stories_dir, stories_file)
        logger.info(f"Reading stories from: {stories_path}")
        stories_content = read_file(stories_path)
        stories = json.loads(stories_content)

        if not stories:
            raise ValueError("No stories found in file")

        # Use the first story
        first_story = stories[0]
        logger.info(f"Processing story: {first_story['summary']}")

        # Generate appropriate code
        if "user creation" in first_story['summary'].lower():
            code = '''def create_user(email: str, password: str, name: str) -> dict:
    """Create a new user."""
    return {
        "email": email,
        "name": name,
        "created_at": "2024-03-20"  # Replace with actual timestamp
    }

if __name__ == "__main__":
    user = create_user("test@example.com", "password123", "Test User")
    print(f"Created user: {user}")
'''
            code_file = os.path.join(programs_dir, "user_creation.py")
        else:
            code = '''def factorial(n: int) -> int:
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    return 1 if n == 0 else n * factorial(n - 1)

if __name__ == "__main__":
    print(f"Factorial of 5: {factorial(5)}")
'''
            code_file = os.path.join(programs_dir, "factorial.py")

        # Save file and update state
        write_file(code_file, code)
        state["code_file"] = code_file
        state["workflow_status"] = "code_generated"

        logger.info(f"Code file saved: {code_file}")
        return code_file

    except Exception as e:
        logger.error(f"Coder Agent error: {e}")
        raise

# Create the Coder Agent
coder_agent = AssistantAgent(
    name="Coder_Agent",
    system_message="""You are a Coder Agent responsible for generating Python code.
Your tasks are:
1. Use the stories file from the /stories folder
2. Generate appropriate Python code based on the stories
3. Include proper docstrings and type hints
4. Save the code in /programs and return the file path""",
    llm_config=LLM_CONFIG,
)

# Register callable
@coder_agent.register_for_execution()
@coder_agent.register_for_llm(name="process_story_to_code", description="Generate code from story file and return path")
def process_story_to_code_wrapper(state: dict) -> str:
    return process_story_to_code(state)
