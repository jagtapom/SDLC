from autogen import ConversableAgent
from src.tools.jira_create_tool import create_jira_story
from src.config.settings import LLM_CONFIG
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def process_stories(state: dict) -> str:
    """Create Jira stories from the stories folder using state."""
    try:
        logger.info("\n=== Jira_Agent Processing Stories ===")
        
        # Define paths
        project_root = str(Path(__file__).parent.parent.parent)
        stories_dir = os.path.join(project_root, "stories")
        stories_file = state.get("stories_file")

        if not stories_file:
            logger.warning("No stories file found in state.")
            return "No stories file found in state."

        stories_path = os.path.join(stories_dir, stories_file)

        if not os.path.exists(stories_path):
            logger.warning(f"Stories file not found: {stories_path}")
            return "Stories file not found"

        # Load stories
        with open(stories_path, 'r') as f:
            stories = json.load(f)

        if not stories:
            logger.warning("No stories found in file.")
            return "No stories to create"

        logger.info(f"Creating {len(stories)} Jira stories...")
        issue_keys = []
        for story in stories:
            if "summary" not in story or "description" not in story:
                logger.warning(f"Invalid story format: {story}")
                continue

            issue_key = create_jira_story({
                "summary": story["summary"],
                "description": story["description"]
            })
            issue_keys.append(issue_key)
            logger.info(f"Created Jira issue: {issue_key}")

        logger.info("✅ Jira story creation complete.")
        state["workflow_status"] = "jira_created"
        state["jira_issues"] = issue_keys

        return "Stories created in Jira"

    except json.JSONDecodeError:
        logger.error("Invalid JSON format in stories file.")
        return "Invalid JSON format"
    except Exception as e:
        logger.error(f"Error in Jira_Agent: {str(e)}")
        return f"Error in Jira_Agent: {str(e)}"

# Define the Jira Agent
jira_agent = ConversableAgent(
    name="Jira_Agent",
    system_message="""You are a Jira Agent.
Tasks:
1. Read stories from the /stories folder
2. Create Jira stories with issue type 'Story' and project 'SDLC'
3. Return 'Stories created in Jira' on success.""",
    llm_config=LLM_CONFIG,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config=False
)

# Register the story processing function
@jira_agent.register_for_execution()
@jira_agent.register_for_llm(description="Create Jira stories from the stories folder.")
def process_stories_wrapper(state: dict) -> str:
    return process_stories(state)
