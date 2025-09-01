from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from tools import search_linkedin_trends, analyze_hashtag_performance
from typing import List, Optional, Dict, Any
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Agent State
class AgentState(TypedDict):
    messages: List[Any]
    topic: str
    tone: str
    audience: str
    length: str
    include_hashtags: bool
    include_cta: bool
    post_count: int
    language: str
    research_data: Optional[str]
    post_strategy: Optional[str]
    generated_posts: List[Dict[str, Any]]
    tokens_used: int

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    api_key = os.getenv("GOOGLE_API_KEY")
    
)

#Agent workflow functions
async def research_phase(state: AgentState) -> AgentState:
    """Research phase: gather information about the topic"""
    try:
        research_data = search_linkedin_trends(state["topic"])
        state["research_data"] = research_data
    except Exception:
        state["research_data"] = f"General insights about {state['topic']}"
    
    return state

async def strategy_phase(state: AgentState) -> AgentState:
    """Strategy phase: develop posting strategy based on inputs"""
    strategy_prompt = ChatPromptTemplate.from_template("""
    You are a LinkedIn content strategist. Based on the following information, create a content strategy for LinkedIn posts:
    
    Topic: {topic}
    Tone: {tone}
    Target Audience: {audience}
    Preferred Length: {length}
    Research Data: {research_data}
    
    Create a strategy that includes:
    1. Key messaging pillars
    2. Content structure recommendations
    3. Engagement tactics
    4. Tone guidelines
    
    Keep it concise but actionable.
    """)
    
    strategy_chain = strategy_prompt | llm
    strategy_response = await strategy_chain.ainvoke({
        "topic": state["topic"],
        "tone": state["tone"],
        "audience": state["audience"],
        "length": state["length"],
        "research_data": state["research_data"]
    })
    
    state["post_strategy"] = strategy_response.content
    state["tokens_used"] += len(strategy_response.content.split()) * 1.3  # Rough token estimate
    
    return state

async def generation_phase(state: AgentState) -> AgentState:
    """Generation phase: create multiple LinkedIn posts"""
    
    # Create structured prompts for each post type
    post_prompts = [
        {
            "approach": "Story/Personal Experience",
            "instruction": "Write a LinkedIn post that tells a personal story or anecdote related to the topic. Make it relatable and authentic."
        },
        {
            "approach": "Data/Insights",
            "instruction": "Write a LinkedIn post that shares interesting data, statistics, or insights about the topic. Make it informative and valuable."
        },
        {
            "approach": "Question/Engagement",
            "instruction": "Write a LinkedIn post that asks thoughtful questions to spark discussion and engagement about the topic."
        },
        {
            "approach": "How-to/Educational",
            "instruction": "Write a LinkedIn post that provides actionable tips or educational content about the topic."
        },
        {
            "approach": "Industry Trends",
            "instruction": "Write a LinkedIn post that discusses current trends and future predictions related to the topic."
        }
    ]
    
    processed_posts = []
    
    for i in range(state["post_count"]):
        prompt_data = post_prompts[i % len(post_prompts)]
        
        # Length guidelines
        length_guide = {
            "short": "Keep it concise, around 100-150 words. Focus on one key point.",
            "medium": "Aim for 150-250 words. Develop the idea with some detail.",
            "long": "Write 250-400 words. Provide comprehensive insights and examples."
        }
        
        individual_prompt = f"""You are an expert LinkedIn content creator. Create a single, high-quality LinkedIn post.

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

        try:
            # Generate individual post
            messages = [
                SystemMessage(content="You are a LinkedIn content expert who creates engaging, professional posts."),
                HumanMessage(content=individual_prompt)
            ]
            
            response = await llm.ainvoke(messages)
            post_content = response.content.strip()
            
            # Get hashtags if requested
            hashtags = []
            if state["include_hashtags"]:
                hashtags = analyze_hashtag_performance(state["topic"])
            
            # Generate CTA if requested
            cta = ""
            if state["include_cta"]:
                if "question" in prompt_data["approach"].lower():
                    cta = "What's your experience with this? Share in the comments! 👇"
                elif "story" in prompt_data["approach"].lower():
                    cta = "Can you relate? Share your own experience below!"
                elif "data" in prompt_data["approach"].lower():
                    cta = "What do these insights mean for your industry? Let me know your thoughts!"
                else:
                    cta = "What are your thoughts on this? I'd love to hear your perspective!"
            
            # Estimate engagement based on approach and content length
            engagement_score = "medium"
            if "question" in prompt_data["approach"].lower() or len(post_content) > 200:
                engagement_score = "high"
            elif len(post_content) < 100:
                engagement_score = "low"
            
            processed_post = {
                "content": post_content,
                "hashtags": hashtags,
                "cta": cta,
                "estimated_engagement": engagement_score,
                "tone_used": state["tone"].title()
            }
            
            processed_posts.append(processed_post)
            state["tokens_used"] += len(response.content.split()) * 1.3
            
        except Exception as e:
            print(f"Error generating post {i+1}: {e}")
            # Create a meaningful fallback post
            fallback_content = f"""🚀 Exploring {state["topic"]}

This is an exciting area that's transforming how we work and think. The potential applications are vast, and we're just scratching the surface.

Key considerations:
• Innovation opportunities
• Implementation challenges  
• Future implications

The landscape is evolving rapidly, and staying informed is crucial for success."""

            fallback_post = {
                "content": fallback_content,
                "hashtags": analyze_hashtag_performance(state["topic"]) if state["include_hashtags"] else [],
                "cta": "What's your take on this? Share your thoughts below!" if state["include_cta"] else "",
                "estimated_engagement": "medium",
                "tone_used": state["tone"].title()
            }
            processed_posts.append(fallback_post)
            state["tokens_used"] += 200
    
    state["generated_posts"] = processed_posts
    return state

# Create the agent workflow
def create_agent_workflow():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("research", research_phase)
    workflow.add_node("strategy", strategy_phase)
    workflow.add_node("generation", generation_phase)
    
    # Add edges
    workflow.set_entry_point("research")
    workflow.add_edge("research", "strategy")
    workflow.add_edge("strategy", "generation")
    workflow.add_edge("generation", END)
    
    return workflow.compile()

# Initialize the agent
Agent = create_agent_workflow()



async def test_generation():
    """Test the agent generation locally"""
    topic_input = input("Enter the topic: ")
    # Test state
    test_state = AgentState(
        messages=[],
        topic=topic_input or "AI in healthcare",
        tone="professional",
        audience="general",
        length="medium",
        include_hashtags=True,
        include_cta=True,
        post_count=3,
        language="english",
        research_data=None,
        post_strategy=None,
        generated_posts=[],
        tokens_used=0
    )
    
    print("\n🤖 Testing agent workflow...")
    
    result = await Agent.ainvoke(test_state)
        
    print(f"\n✅ Generation completed!")
    print(f"Posts generated: {len(result['generated_posts'])}")
    print(f"Tokens used: {result['tokens_used']}")
        
        # Print first post sample
    if result['generated_posts']:
        first_post = result['generated_posts'][0]
        print(f"\n📝 Sample post:")
        print(f"Content preview: {first_post['content']}...")
        print(f"Hashtags: {first_post['hashtags'][:3]}")
        print(f"CTA: {first_post['cta']}")
        
        
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(test_generation())
