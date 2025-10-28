from typing import List
import json
import random
from datetime import datetime, timedelta
import importlib

# Graceful fallbacks for optional dependencies, using dynamic imports

# Message classes stubs
class BaseMessage:
    def __init__(self, content: str = ""):
        self.content = content

class HumanMessage(BaseMessage):
    pass

class AIMessage(BaseMessage):
    pass

try:
    _msgs = importlib.import_module("langchain_core.messages")
    HumanMessage = getattr(_msgs, "HumanMessage", HumanMessage)  # type: ignore
    AIMessage = getattr(_msgs, "AIMessage", AIMessage)  # type: ignore
    BaseMessage = getattr(_msgs, "BaseMessage", BaseMessage)  # type: ignore
except ImportError:
    pass

# tool decorator fallback

def tool(func=None, **kwargs):
    if func is None:
        def _wrap(f):
            return f
        return _wrap
    return func

try:
    _tools_mod = importlib.import_module("langchain_core.tools")
    tool = getattr(_tools_mod, "tool", tool)  # type: ignore
except Exception:
    pass

# ChatOpenAI stub and dynamic import
class ChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass

try:
    _lco = importlib.import_module("langchain_openai")
    ChatOpenAI = getattr(_lco, "ChatOpenAI", ChatOpenAI)  # type: ignore
except Exception:
    pass

# create_react_agent fallback

def create_react_agent(llm, tools, prompt):
    class _DummyAgent:
        def invoke(self, *_args, **_kwargs):
            return {"messages": [AIMessage(content="Dependencies not installed. Please install project dependencies to use the agent.")]}
    return _DummyAgent()

try:
    _lg = importlib.import_module("langgraph.prebuilt")
    create_react_agent = getattr(_lg, "create_react_agent", create_react_agent)  # type: ignore
except Exception:
    pass

# load_dotenv dynamic import

def load_dotenv(*args, **kwargs):
    return False

try:
    _dotenv = importlib.import_module("dotenv")
    load_dotenv = getattr(_dotenv, "load_dotenv", load_dotenv)  # type: ignore
except Exception:
    pass

load_dotenv()


# -------- Tools --------
@tool
def write_json(filepath: str, data: dict) -> str:
    """Write a Python dictionary as JSON to a file with pretty formatting."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return f"Successfully wrote JSON data to '{filepath}' ({len(json.dumps(data))} characters)."
    except Exception as e:
        return f"Error writing JSON: {str(e)}"


@tool
def read_json(filepath: str) -> str:
    """Read and return the contents of a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in file - {str(e)}"
    except Exception as e:
        return f"Error reading JSON: {str(e)}"


@tool
def generate_sample_users(
        first_names: List[str],
        last_names: List[str],
        domains: List[str],
        min_age: int,
        max_age: int
) -> dict:
    """
    Generate sample user data. Count is determined by the length of first_names.

    Args:
        first_names: List of first names (one per user)
        last_names: List of last names (will cycle if fewer than first_names)
        domains: List of email domains (will cycle through)
        min_age: Minimum age for users
        max_age: Maximum age for users

    Returns:
        Dictionary with 'users' array or 'error' message
    """
    # Validation
    if not first_names:
        return {"error": "first_names list cannot be empty"}
    if not last_names:
        return {"error": "last_names list cannot be empty"}
    if not domains:
        return {"error": "domains list cannot be empty"}
    if min_age > max_age:
        return {"error": f"min_age ({min_age}) cannot be greater than max_age ({max_age})"}
    if min_age < 0 or max_age < 0:
        return {"error": "ages must be non-negative"}

    users = []
    count = len(first_names)

    for i in range(count):
        first = first_names[i]
        last = last_names[i % len(last_names)]
        domain = domains[i % len(domains)]
        email = f"{first.lower()}.{last.lower()}@{domain}"

        user = {
            "id": i + 1,
            "firstName": first,
            "lastName": last,
            "email": email,
            "username": f"{first.lower()}{random.randint(100, 999)}",
            "age": random.randint(min_age, max_age),
            "registeredAt": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        }
        users.append(user)

    return {"users": users, "count": len(users)}


TOOLS = [write_json, read_json, generate_sample_users]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SYSTEM_MESSAGE = (
    "You are the 'Scholarship Ball Funding Agent' for the organisation: Women's Leadership Initiative, "
    "whose mission is: 'Empowering undergraduate women through leadership scholarships in New York State.'\n"
    "Your role is to discover, prioritise, apply for, and track the deposit and allocation of funding "
    "(grants, scholarships, sponsorships) in support of the annual Scholarship Ball and the associated "
    "scholarship awards. You will operate as a ReAct agent: you may call tools to complete your tasks.\n\n"
    "Your responsibilities include:\n"
    "- Opportunity Discovery: Search available grant/funding databases for opportunities aligned with our mission "
    "(women's leadership, undergraduate scholarships, community service, regional grants) and generate a short list with fit scores.\n"
    "- Prioritisation & Workflow Generation: For each discovered opportunity, compute a 'fit score' "
    "(based on mission alignment, award size, deadline, geographic match, effort required).\n"
    "- Application Management: For selected opportunities, create a checklist of tasks (narrative, budget, "
    "documentation, submission), generate a draft outline for the application, and track submission status.\n"
    "- Donor & Sponsorship Integration: Identify high-potential sponsors/donors (corporate, alumni), "
    "generate personalised outreach templates, track responses.\n"
    "- Deposit & Allocation Tracking: Once funding is awarded, track deposit receipt, allocate to scholarships "
    "or event costs, monitor status, generate recognition materials.\n"
    "- Dashboard & Alerts: Provide timely alerts (e.g., upcoming deadlines, overdue tasks, deposit missing), "
    "supply periodic summary of pipeline, next steps and metrics.\n\n"
    "Constraints & Instructions:\n"
    "- Use only approved tools. Do not attempt to invent tools; reason about which tool to call, then call it.\n"
    "- When using a tool, you must output the call in the format required by LangChain tool calling (tool name, input arguments).\n"
    "- After each tool call, observe the output, update your reasoning, and decide the next step or whether you have completed the task.\n"
    "- Provide structured JSON output when appropriate (e.g., list of opportunities, tasks list, dashboard summary) "
    "and also provide human-readable narrative.\n"
    "- Clearly label whether certain data is simulated/mock or live API derived.\n"
    "- Always keep the mission and organisation context front of mind when prioritising opportunities and drafting texts.\n"
    "- The loop continues until you produce a final answer for the user.\n\n"
    "You are now ready. Ask the user: 'What would you like to begin with—discover funding opportunities, "
    "generate donor outreach, or track deposit status?'"
)

agent = create_react_agent(llm, TOOLS, prompt=SYSTEM_MESSAGE)


def run_agent(user_input: str, history: List[BaseMessage]) -> AIMessage:
    """Single-turn agent runner with automatic tool execution via LangGraph."""
    try:
        result = agent.invoke(
            {"messages": history + [HumanMessage(content=user_input)]},
            config={"recursion_limit": 50}
        )
        # Return the last AI message
        return result["messages"][-1]
    except Exception as e:
        # Return error as an AI message so the conversation can continue
        return AIMessage(
            content=f"Error: {str(e)}\n\nPlease try rephrasing your request or provide more specific details.")


if __name__ == "__main__":
    print("=" * 60)
    print("Scholarship Ball Funding Agent - Sample Data Generator")
    print("=" * 60)
    print("Generate sample user data and save to JSON files.")
    print()
    print("Examples:")
    print("  - Generate funding opportunities for high shcool scholarships and save to funding_opportunities.json")
    print("  - Create opportunities with award sizes over $10,000")
    print("  - Create nationwide opportunities with a fit score above 80.")
    print()
    print("Commands: 'quit' or 'exit' to end")
    print("=" * 60)

    history: List[BaseMessage] = []

    while True:
        user_input = input("\nYou: ").strip()

        # Check for exit commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        print("\nAgent: ", end="", flush=True)
        response = run_agent(user_input, history)
        print(response.content)

        # Update conversation history
        history += [HumanMessage(content=user_input), response]