# Prompts 
generator_prompt = f"""You are an expert LinkedIn content creator. Create a single, high-quality LinkedIn post.

TOPIC: {state["topic"]}
APPROACH: {prompt_data["approach"]}
INSTRUCTION: {prompt_data["instruction"]}

REQUIREMENTS:
- Tone: {state["tone"]}
- Target Audience: {state["audience"]}
- Length: {length_guide[state["length"]]}
- Language: {state["language"]}

CONTENT STRATEGY: {state["post_strategy"]}

RESEARCH INSIGHTS: {state["research_data"][:500] if state["research_data"] else "No specific research data available"}

Write an engaging LinkedIn post that:
1. Hooks readers in the first line
2. Provides value to the target audience
3. Uses the specified tone consistently
4. Follows the {prompt_data["approach"]} approach
5. Includes line breaks for readability
6. Ends with engagement (if this is a question/engagement post)

IMPORTANT: Write only the post content, no additional text or explanations."""