import json
from google.genai import types
from prompts import (
    HABIT_ANALYZER_SYSTEM_PROMPT,
    JUDGE_EVAL_PROMPT,
    JUDGE_SYSTEM_PROMPT,
    PLAN_WRITER_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
)


class AgentExecutionError(Exception):
    def __init__(self, user_message: str, original_error: Exception | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.original_error = original_error


tavily_decl = types.FunctionDeclaration(
    name="tavily_search_tool",
    description="Search the web for evidence-based burnout recovery techniques, therapist advice, and recovery stories.",
    parameters=types.Schema(
        type="object",
        properties={
            "query": types.Schema(
                type="string",
                description="The search query string",
            )
        },
        required=["query"],
    ),
)


def _is_quota_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        "resource_exhausted" in message
        or "quota exceeded" in message
        or "429" in message
    )


def _raise_agent_error(agent_name: str, error: Exception) -> None:
    if _is_quota_error(error):
        raise AgentExecutionError(
            f"{agent_name} could not use Gemini because the API quota is exhausted.",
            original_error=error,
        ) from error

    raise AgentExecutionError(
        f"{agent_name} failed because the Gemini request returned an unexpected error.",
        original_error=error,
    ) from error


def _run_tavily_search(query: str, tavily_client) -> str:
    result = tavily_client.search(query=query, max_results=5)
    snippets = []
    for item in result.get("results", []):
        title = item.get("title", "Untitled")
        content = item.get("content", "")
        snippets.append(f"- {title}: {content[:200]}")
    return "\n".join(snippets)


def _extract_sections(user_profile: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    for line in user_profile.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        sections[key.strip().lower()] = value.strip()
    return sections


def _extract_research_topics(user_profile: str) -> list[str]:
    sections = _extract_sections(user_profile)
    triggers = sections.get("stress triggers", "")
    topics = [chunk.strip() for chunk in triggers.split(",") if chunk.strip()]
    if not topics:
        topics = [
            "burnout recovery routines",
            "sleep recovery habits",
            "stress reduction micro habits",
        ]
    return topics[:3]


def fallback_research_brief(tavily_client, user_profile: str) -> str:
    topics = _extract_research_topics(user_profile)
    sections = [
        "## Fallback Research Brief",
        "Gemini quota was unavailable, so this brief was assembled from Tavily results and built-in burnout recovery guidance.",
    ]

    for topic in topics:
        query = f"evidence based burnout recovery {topic}"
        snippets = _run_tavily_search(query, tavily_client)
        if snippets:
            sections.append(f"### Search Focus: {topic}")
            sections.append(snippets)

    sections.append("### Practical recovery themes")
    sections.append(
        "- Lower the incoming load first with fewer after-hours demands, clearer boundaries, and protected breaks.\n"
        "- Rebuild basic regulation through consistent sleep timing, regular meals, hydration, and light movement.\n"
        "- Prefer micro-habits over ambitious routines because burnout usually reduces energy, focus, and follow-through.\n"
        "- Add emotional processing through brief journaling, reflection prompts, or support from one trusted person."
    )
    return "\n\n".join(sections)


def fallback_habit_analysis(research_brief: str, user_profile: str) -> str:
    sections = _extract_sections(user_profile)
    work_situation = sections.get("work situation", "Your workload appears heavy and draining.")
    stress_triggers = sections.get("stress triggers", "Your stress triggers suggest ongoing overload.")
    lifestyle = sections.get("lifestyle", "Your current routines suggest recovery capacity is low.")

    return f"""## Fallback Habit Analysis
Gemini quota was unavailable, so this analysis uses rule-based matching from your profile and the research brief.

### Burnout pattern
- Work situation: {work_situation}
- Stress triggers: {stress_triggers}
- Lifestyle: {lifestyle}

### Best-fit techniques
- Boundary reset: reduce one source of work spillover each day so the stress load stops compounding.
- Nervous system downshift: use a 5-minute breathing, stretching, or quiet reset when stress peaks.
- Energy protection: simplify meals, hydration, and movement so recovery does not depend on high motivation.
- Evening decompression: use one short check-in question and a lighter screen routine before bed.

### Why these fit
- They are realistic when energy is low.
- They target overload and recovery capacity at the same time.
- They create early wins without turning healing into another performance task.

### Planning principle
Start with stabilization, then add structure only after the smallest habits begin to feel repeatable.
"""


def fallback_recovery_plan(research_brief: str, habit_analysis: str, user_profile: str) -> str:
    days = [
        ("Day 1", "Drink water before checking your phone", "What feels heaviest right now?", "Reduce pressure by doing the minimum viable version of today."),
        ("Day 2", "Take 5 slow breaths before work", "When did I feel most tense today?", "Notice your main stress spike without trying to fix everything."),
        ("Day 3", "Step outside for 5 minutes in the morning", "What gave me even 1% relief today?", "Get one brief change of environment."),
        ("Day 4", "Eat something nourishing within 90 minutes of waking", "Did I skip my own needs today?", "Support energy with regular food instead of running on stress."),
        ("Day 5", "Do a 5-minute shoulder and neck stretch", "What task drained me the fastest?", "Release physical tension from accumulated stress."),
        ("Day 6", "Write one sentence naming today's priority", "What can wait until later?", "Lower overload by choosing one essential focus."),
        ("Day 7", "Sit quietly for 5 minutes with no input", "What helped me slow down this week?", "Make rest feel allowed, not earned."),
        ("Day 8", "Take a short walk after waking or lunch", "What routine felt easiest to keep?", "Reintroduce light movement to support recovery."),
        ("Day 9", "Start work with one task before checking messages", "Did focus feel easier or harder today?", "Protect attention from immediate digital overwhelm."),
        ("Day 10", "Send one honest check-in to a trusted person", "How did connection affect my stress?", "Reduce isolation with a small social touchpoint."),
        ("Day 11", "Prepare a simple snack or meal ahead of time", "What improved my energy today?", "Make nourishment more automatic."),
        ("Day 12", "Do 5 minutes of box breathing or gentle stretching", "What helped my body settle?", "Build a repeatable stress-reset ritual."),
        ("Day 13", "Block one small break on your calendar", "Did I protect any recovery time today?", "Practice treating rest like a real commitment."),
        ("Day 14", "List 3 tasks, then choose only 1 must-do", "What happened when I reduced my expectations?", "Strengthen realistic planning."),
        ("Day 15", "Review your week before starting the day", "What pattern do I want to keep?", "Shift from recovery mode into sustainable structure."),
        ("Day 16", "Take a 10-minute walk without your phone", "Did unplugging change my stress level?", "Create a deeper mental reset."),
        ("Day 17", "Begin work with a clear stop time in mind", "Did a stopping point make the day feel safer?", "Practice healthier work boundaries."),
        ("Day 18", "Choose one meaningful non-work activity for later", "What brought back a little energy or identity?", "Reconnect with life outside productivity."),
        ("Day 19", "Tidy or reset one small physical space", "Did my environment affect my mood?", "Use a small environmental reset to support calm."),
        ("Day 20", "Write one sentence about what burnout has taught you", "What do I want to protect going forward?", "Turn reflection into a sustainable recovery lesson."),
        ("Day 21", "Pick 3 habits to carry forward", "Which habits feel supportive rather than forced?", "Finish with a gentle maintenance plan."),
    ]

    sections = [
        "## 21-Day Burnout Recovery Plan",
        "Gemini quota was unavailable, so this plan was generated from a built-in fallback template designed for burnout recovery pacing.",
        "### Week 1: Rest and stabilization",
    ]

    for index, (day, morning, evening, focus) in enumerate(days, start=1):
        if index == 8:
            sections.append("### Week 2: Rebuilding")
        if index == 15:
            sections.append("### Week 3: Reintegration")
        sections.append(
            f"**{day}**\n"
            f"- Morning micro-habit: {morning}\n"
            f"- Main focus: {focus}\n"
            f"- Evening check-in: {evening}"
        )

    sections.append("### Notes")
    sections.append(
        "- If a day feels too hard, repeat the gentlest version of the previous day.\n"
        "- The goal is steadiness, not perfect completion.\n"
        "- If symptoms feel severe or long-lasting, a licensed mental health professional can help personalize the plan further."
    )
    return "\n\n".join(sections)


def fallback_judge_result() -> dict:
    return {
        "scores": {
            "scientific_grounding": {
                "score": 3,
                "reasoning": "Fallback mode uses common evidence-aligned recovery principles, but the plan was not fully model-evaluated.",
            },
            "personalization": {
                "score": 3,
                "reasoning": "The fallback plan is lightly tailored to burnout constraints, though less personalized than the Gemini path.",
            },
            "practicality": {
                "score": 4,
                "reasoning": "The actions are intentionally small and realistic for someone with low energy.",
            },
            "progression": {
                "score": 4,
                "reasoning": "The plan clearly moves from stabilization to rebuilding to reintegration.",
            },
            "compassionate_tone": {
                "score": 4,
                "reasoning": "The wording stays gentle and non-pressuring.",
            },
        },
        "overall_score": 3.6,
        "summary": "Fallback mode produced a practical recovery plan, but the rubric was estimated without the Gemini judge step.",
        "top_strength": "Gentle pacing and low-effort habits that suit burnout recovery.",
        "top_improvement": "Use an active Gemini quota to get deeper personalization and a real LLM-based evaluation.",
    }


def burnout_researcher_agent(client, tavily_client, user_profile: str, log_step=None) -> str:
    if log_step:
        log_step("Researcher: searching for burnout recovery techniques")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=(
                        f"Research evidence-based burnout recovery techniques for this person: {user_profile}. "
                        "Use the search tool to find specific techniques, therapist advice, and recovery stories. "
                        "Then produce a research brief."
                    )
                )
            ],
        )
    ]

    tools = [types.Tool(function_declarations=[tavily_decl])]

    for turn in range(8):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=RESEARCHER_SYSTEM_PROMPT,
                    tools=tools,
                ),
            )
        except Exception as error:
            _raise_agent_error("Researcher", error)

        parts = response.candidates[0].content.parts
        function_calls = [part.function_call for part in parts if part.function_call]

        if not function_calls:
            final_text = "".join(part.text for part in parts if part.text)
            if log_step:
                log_step(f"Researcher: done in {turn + 1} turn(s)")
            return final_text

        contents.append(types.Content(role="model", parts=parts))

        tool_results = []
        for function_call in function_calls:
            query = function_call.args.get("query", "burnout recovery")
            if log_step:
                log_step(f"Researcher: searching -> '{query}'")
            search_result = _run_tavily_search(query, tavily_client)
            tool_results.append(
                types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": search_result},
                )
            )

        contents.append(types.Content(role="user", parts=tool_results))

    if log_step:
        log_step("Researcher: max turns reached")
    return "".join(part.text for part in parts if part.text)


def habit_analyzer_agent(client, research_brief: str, user_profile: str, log_step=None) -> str:
    if log_step:
        log_step("Habit Analyzer: mapping techniques to user's situation")

    prompt = f"""Analyze this person's burnout situation and map recovery techniques to their specific triggers.

USER PROFILE:
{user_profile}

RESEARCH BRIEF:
{research_brief}

Map the most relevant techniques to this person's specific situation.
Explain why each technique fits their triggers and lifestyle."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=HABIT_ANALYZER_SYSTEM_PROMPT,
            ),
        )
    except Exception as error:
        _raise_agent_error("Habit Analyzer", error)

    if log_step:
        log_step("Habit Analyzer: analysis complete")
    return response.text


def plan_writer_agent(client, research_brief: str, habit_analysis: str, user_profile: str, log_step=None) -> str:
    if log_step:
        log_step("Plan Writer: building 21-day recovery plan")

    prompt = f"""Write a complete 21-day burnout recovery plan for this person.

USER PROFILE:
{user_profile}

RESEARCH BRIEF:
{research_brief}

HABIT ANALYSIS:
{habit_analysis}

Write the full 21-day plan now. Follow all rules in your instructions."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=PLAN_WRITER_SYSTEM_PROMPT,
            ),
        )
    except Exception as error:
        _raise_agent_error("Plan Writer", error)

    if log_step:
        log_step("Plan Writer: 21-day plan ready")
    return response.text


def judge_agent(client, user_profile: str, research_brief: str, recovery_plan: str, log_step=None) -> dict:
    if log_step:
        log_step("Judge: evaluating plan quality")

    eval_prompt = JUDGE_EVAL_PROMPT.format(
        user_profile=user_profile,
        research_brief=research_brief,
        recovery_plan=recovery_plan,
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=eval_prompt)],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_SYSTEM_PROMPT,
            ),
        )
    except Exception as error:
        _raise_agent_error("Judge", error)

    raw = response.text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "scores": {
                "scientific_grounding": {"score": 0, "reasoning": "Could not parse"},
                "personalization": {"score": 0, "reasoning": "Could not parse"},
                "practicality": {"score": 0, "reasoning": "Could not parse"},
                "progression": {"score": 0, "reasoning": "Could not parse"},
                "compassionate_tone": {"score": 0, "reasoning": "Could not parse"},
            },
            "overall_score": 0,
            "summary": "Judge response could not be parsed.",
            "top_strength": "N/A",
            "top_improvement": "N/A",
        }

    if log_step:
        log_step(f"Judge: overall score = {result.get('overall_score', '?')}/5")
    return result
