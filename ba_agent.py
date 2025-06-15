from autogen import ConversableAgent
from src.config.settings import LLM_CONFIG
from src.tools.file_read_tool import read_file
import logging
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_requirements_wrapper(file_path: str, state: dict) -> str:
    try:
        logger.info("\n=== BA Agent Starting ===")
        logger.info(f"Processing requirements file: {file_path}")

        # Get stories directory
        project_root = str(Path(__file__).parent.parent.parent)
        stories_dir = os.path.join(project_root, "stories")
        logger.info(f"Stories directory: {stories_dir}")

        os.makedirs(stories_dir, exist_ok=True)

        file_content = read_file(file_path)
        logger.info(f"File content length: {len(file_content)} characters")

        stories = []
        for line in file_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit() and '.' in line or line.startswith('-'):
                if line.startswith('-'):
                    line = line[1:].strip()
                story = {
                    "summary": f"As a user, I want to {line.lower()}",
                    "description": f"""User Story:
As a user,
I want to {line.lower()}
So that I can achieve my goal efficiently

Acceptance Criteria:
1. The system should implement {line}
2. The feature should be user-friendly
3. The implementation should follow best practices

Technical Notes:
- Priority: Medium
- Story Points: 3
- Dependencies: None""",
                    "priority": "Medium",
                    "story_points": 3,
                    "type": "User Story"
                }
                stories.append(story)
                logger.info(f"Generated user story: {story['summary']}")

        logger.info(f"Total user stories generated: {len(stories)}")
        uploaded_filename = os.path.basename(file_path)
        stories_file = f"stories_{uploaded_filename}"
        stories_path = os.path.join(stories_dir, stories_file)

        with open(stories_path, 'w') as f:
            json.dump(stories, f, indent=2)

        logger.info(f"Successfully saved {len(stories)} user stories")

        state["stories_file"] = stories_file
        state["workflow_status"] = "stories_generated"

        logger.info("\n=== Generated User Stories ===")
        for i, story in enumerate(stories, 1):
            logger.info(f"\nStory {i}:")
            logger.info(f"Summary: {story['summary']}")
            logger.info(f"Description: {story['description']}")
            logger.info(f"Priority: {story['priority']}")
            logger.info(f"Story Points: {story['story_points']}")
            logger.info(f"Type: {story['type']}")

        logger.info("\n=== BA Agent Completed ===")
        return f"Generated and saved {len(stories)} user stories to {stories_path}"

    except Exception as e:
        logger.error(f"Error processing requirements: {str(e)}")
        return f"Error processing requirements: {str(e)}"


ba_agent = ConversableAgent(
    name="BA_Agent",
    system_message="""You are a Business Analyst Agent (BA_Agent). Your role is to:
    1. Read requirements from a file using process_requirements_wrapper
    2. Convert requirements into proper user stories with:
       - Clear \"As a user, I want to...\" format
       - Detailed acceptance criteria
       - Technical notes
       - Story points and priority
    3. Save stories to the /stories folder
    4. Log all actions and errors

    Example output format:
    {
        \"summary\": \"As a user, I want to create an account\",
        \"description\": \"User Story: As a user, I want to create an account...\",
        \"priority\": \"Medium\",
        \"story_points\": 3,
        \"type\": \"User Story\"
    }""",
    llm_config=LLM_CONFIG,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "workspace",
        "use_docker": False,
        "timeout": 60
    }
)

@ba_agent.register_for_execution()
@ba_agent.register_for_llm(name="process_requirements_wrapper", description="Process requirements file and generate Jira stories.")
def process_requirements_wrapper_func(file_path: str, state: dict) -> str:
    return process_requirements_wrapper(file_path, state)
