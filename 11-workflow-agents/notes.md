# Module 11 — official documentation cross-reference

| Topic | Page |
|---|---|
| Workflow agents overview | https://adk.dev/agents/workflow-agents/ |
| SequentialAgent | https://adk.dev/agents/workflow-agents/sequential-agents/ |
| ParallelAgent | https://adk.dev/agents/workflow-agents/parallel-agents/ |
| LoopAgent | https://adk.dev/agents/workflow-agents/loop-agents/ |
| Multi-agent patterns | https://adk.dev/workflows/patterns/ |
| Workflow (graph) — the replacement | https://adk.dev/graphs/ (Module 13) |

## Confirmed on this machine (ADK 2.8.0, Vertex, gemini-2.5-flash, 2026-09-05)

- **All three are DEPRECATED** in ADK 2.8:
  `"SequentialAgent/ParallelAgent/LoopAgent is deprecated in favor of Workflow and will
  be removed in a future version. Workflow cannot yet be used as an LlmAgent sub-agent."`
  Still functional; still needed where `Workflow` can't nest. Patterns transfer 1:1.
- `from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent, BaseAgent`.
- **SequentialAgent** (ex01): `sub_agents=[...]` run in order, one shared `InvocationContext`;
  each step's `output_key` is readable as `{key}` in later steps' instructions. Verified:
  spec→writer(`draft`)→reviewer(`review`)→refactor(`final`); `state` ends with all three.
- **ParallelAgent** (ex02): branches start together. Verified concurrent — 3 researchers
  finished at 6.9/7.7/8.8s (not summed). No shared history between branches; they meet
  only via `output_key`s. Merge in a following `SequentialAgent` step reading `{solar}`
  `{wind}` `{hydro}`.
- **LoopAgent** (ex03): `LoopAgent(name=, max_iterations=N, sub_agents=[...])`. Does NOT
  stop itself. Stop by: `max_iterations`, or a sub-`BaseAgent` that
  `yield Event(actions=EventActions(escalate=True))`. State carries between iterations.
  ⚠️ A custom stop-checker that writes `ctx.session.state[k]=v` **directly** does NOT
  persist — write via `EventActions(state_delta={k: v})` on the yielded Event (verified).
- `LoopAgent` sig also has: `retry_config`, `timeout`, `wait_for_output`, `input_schema`,
  `output_schema`, `state_schema`, `before/after_agent_callback`.

## Imports

```python
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent, BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions   # escalate=True, state_delta={}
```

examples :

ex01_sequential_pipeline (you type a function spec; it writes the function, reviews it, then refactors it)
- c
- Parse a 'HH:MM' string into total minutes since midsnight;

A tagline for a bakery that mentions bread. Rule for the critic: the first draft must always be rejected with a suggestion for improvement.

ex01_sequential_pipeline: SequentialAgent (code_pipeline)

Flow: your message goes into state["spec"]. Then writer produces draft, reviewer produces review, and refactor produces final.

Each step reads the previous step's output through {placeholders}, so describe a single Python function:

- A function that checks if a string is a palindrome, ignoring case and punctuation
- Parse a date string like "2024-03-15" and return the day of the week; handle invalid input
- Merge two sorted lists into one sorted list without using sort()
- Compute the nth Fibonacci number efficiently, raising ValueError for negative n
- Flatten an arbitrarily nested list of integers
- Validate an email address with a regex and return True/False

What to watch: the Events panel shows three agents taking turns. Open the State tab to see spec, draft, review and final fill in one after another. Vague specs like "sorting function" give the reviewer more to criticise.

---

ex02_parallel_gather: ParallelAgent + SequentialAgent (research_then_synth)

Flow: your message goes into state["topic"]. Three researchers then run at the same time: cost, benefits and risks. Finally the synthesizer combines their notes into 3 sentences.

Give it a topic that has costs, benefits and risks:

- Solar panels for a home
- Moving a monolith to microservices
- Electric cars
- Remote work for software teams
- Adopting Kubernetes for a small startup
- Getting a master's degree in computer science

What to watch: the three researcher events can show up in any order, which shows they run in parallel. Then the synthesizer runs. The State tab will contain topic, cost, benefits and risks.

---

ex03_loop_refinement: LoopAgent (refine)

Flow: your message goes into state["rubric"]. The agent then repeats writer → critic → stopper up to 3 times. The loop ends early once the critic replies APPROVED, because the stopper then sets escalate=True.

Your message should be a writing task plus checkable rules. Strict rules give you more loop rounds:

- Write a haiku about coffee. Rules: exactly 5-7-5 syllables, must mention "morning", no word "cup".
- Write a product tagline for a running shoe. Rules: under 8 words, must contain a verb, no exclamation marks.
- Write a tweet announcing a Python library release. Rules: under 200 characters, include one emoji, mention "v2.0", end with a question.
- Write a limerick about a cat who codes. Rules: AABBA rhyme scheme, must include the word "bug".
- Write a one-sentence error message for a failed login. Rules: polite, under 15 words, don't blame the user, suggest a next step.
- Easy, approves in round 1: Write the word hello in uppercase.
- Hard, likely hits the 3-round limit: Write a sentence of exactly 12 words where every word starts with the letter S.
