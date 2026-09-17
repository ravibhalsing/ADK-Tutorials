"""The CrewAI wrapping pattern (reference — not run here).

    pip install "google-adk[extensions]"   # or: pip install crewai-tools

CrewAI tools need an explicit name + description because ADK can't always infer
them from the CrewAI object.
"""

# from crewai_tools import SerperDevTool          # a CrewAI web-search tool
# from google.adk.integrations.crewai import CrewaiTool   # (or google.adk.tools.crewai_tool)
# from google.adk.agents import Agent
#
# serper = SerperDevTool()   # needs SERPER_API_KEY
#
# search_tool = CrewaiTool(
#     tool=serper,
#     name="web_search",
#     description="Search the web for current information. Input: a search query string.",
# )
#
# agent = Agent(
#     name="researcher",
#     model="gemini-2.5-flash",
#     instruction="Use web_search for anything recent, then summarize with sources.",
#     tools=[search_tool],
# )

PATTERN = """
CrewaiTool(tool=<crewai tool instance>, name="<snake_case>", description="<what + input>")
"""
