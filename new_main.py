# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import asyncio
import json
from dataclasses import dataclass
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangChain/LangGraph imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain_community.tools import DuckDuckGoSearchResults  # Changed import

app = FastAPI(title="LinkedIn Post Generator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PostRequest(BaseModel):
    topic: str
    tone: Optional[str] = "professional"
    audience: Optional[str] = "general"
    length: Optional[str] = "medium"
    include_hashtags: Optional[bool] = True
    include_cta: Optional[bool] = True
    post_count: Optional[int] = 3
    language: Optional[str] = "english"

class Citation(BaseModel):
    title: str
    link: str
    snippet: str

class LinkedInPost(BaseModel):
    content: str
    hashtags: List[str]
    cta: str
    estimated_engagement: str
    tone_used: str

class GenerationResponse(BaseModel):
    posts: List[LinkedInPost]
    generation_time: float
    tokens_used: int
    cost_estimate: float
    search_results_used: bool
    citations: List[Citation]  # Added citations field

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
    citations: List[Dict[str, str]]  # Added citations to state

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
)

# Tools
@tool
def search_linkedin_trends(topic: str) -> Dict[str, Any]:
    """Search for current trends and popular content related to the topic on LinkedIn and web."""
    try:
        # Use DuckDuckGoSearchResults with JSON output to get URLs
        search = DuckDuckGoSearchResults(output_format="json", max_results=5)
        
        query = f"LinkedIn {topic} trending posts 2024 2025"
        results_json = search.run(query)
        
        # Parse the JSON results
        results = json.loads(results_json)
        
        # Extract citations
        citations = []
        research_text = f"Research findings for {topic}:\n\n"
        
        for i, result in enumerate(results[:3]):  # Limit to top 3 results
            title = result.get('title', 'Untitled')
            link = result.get('link', '')
            snippet = result.get('snippet', '')
            
            citations.append({
                'title': title,
                'link': link,
                'snippet': snippet
            })
            
            research_text += f"{i+1}. {title}\n{snippet[:200]}...\n\n"
        
        return {
            'research_text': research_text[:1000],
            'citations': citations
        }
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {
            'research_text': f"Search unavailable for {topic}: {str(e)}",
            'citations': []
        }

@tool
def analyze_hashtag_performance(topic: str) -> List[str]:
    """Generate relevant hashtags based on the topic and current LinkedIn trends."""
    hashtag_map = {
        "startup": ["#StartupLife", "#Entrepreneurship", "#Innovation", "#TechStartup", "#ScaleUp"],
        "ai": ["#ArtificialIntelligence", "#MachineLearning", "#AI", "#TechInnovation", "#FutureOfWork"],
        "marketing": ["#Marketing", "#DigitalMarketing", "#ContentMarketing", "#MarketingStrategy", "#GrowthHacking"],
        "leadership": ["#Leadership", "#Management", "#ExecutiveLeadership", "#TeamBuilding", "#WorkplaceCulture"],
        "technology": ["#Technology", "#TechTrends", "#Innovation", "#DigitalTransformation", "#TechLeadership"],
        "career": ["#CareerGrowth", "#ProfessionalDevelopment", "#CareerAdvice", "#JobSearch", "#NetworkingTips"]
    }
    
    # Simple keyword matching for demo
    for key, tags in hashtag_map.items():
        if key.lower() in topic.lower():
            return tags
    
    return ["#LinkedIn", "#Professional", "#Insights", "#Growth", "#Success"]

# Agent workflow functions
async def research_phase(state: AgentState) -> AgentState:
    """Research phase: gather information about the topic"""
    try:
        search_result = search_linkedin_trends(state["topic"])
        state["research_data"] = search_result['research_text']
        state["citations"] = search_result['citations']
    except Exception as e:
        logger.error(f"Research phase error: {str(e)}")
        state["research_data"] = f"General insights about {state['topic']}"
        state["citations"] = []
    
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
            logger.error(f"Error generating post {i+1}: {e}")
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
agent = create_agent_workflow()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LinkedIn Post Generator API", "status": "running"}

@app.post("/generate-posts", response_model=GenerationResponse)
async def generate_posts(request: PostRequest):
    """Generate LinkedIn posts using the agentic workflow"""
    start_time = time.time()
    
    logger.info(f"Starting generation for topic: {request.topic}")
    
    try:
        # Validate OpenAI API key
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-openai-api-key-here":
            raise HTTPException(status_code=500, detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        
        # Initialize state
        initial_state = AgentState(
            messages=[],
            topic=request.topic,
            tone=request.tone,
            audience=request.audience,
            length=request.length,
            include_hashtags=request.include_hashtags,
            include_cta=request.include_cta,
            post_count=min(request.post_count, 5),  # Limit to 5 posts max
            language=request.language,
            research_data=None,
            post_strategy=None,
            generated_posts=[],
            tokens_used=0,
            citations=[]  # Initialize citations
        )
        
        logger.info("Running agent workflow...")
        
        # Run the agent workflow
        final_state = await agent.ainvoke(initial_state)
        
        logger.info(f"Generated {len(final_state['generated_posts'])} posts")
        
        # Calculate metrics
        generation_time = time.time() - start_time
        tokens_used = final_state["tokens_used"]
        cost_estimate = tokens_used * 0.00002  # Rough estimate for GPT-4o-mini
        
        # Convert to response format
        posts = []
        for post_data in final_state["generated_posts"]:
            post = LinkedInPost(
                content=post_data["content"],
                hashtags=post_data["hashtags"],
                cta=post_data["cta"],
                estimated_engagement=post_data["estimated_engagement"],
                tone_used=post_data["tone_used"]
            )
            posts.append(post)
        
        # Convert citations
        citations = []
        for citation_data in final_state.get("citations", []):
            citation = Citation(
                title=citation_data["title"],
                link=citation_data["link"],
                snippet=citation_data["snippet"]
            )
            citations.append(citation)
        
        logger.info(f"Successfully generated {len(posts)} posts in {generation_time:.2f}s")
        
        return GenerationResponse(
            posts=posts,
            generation_time=round(generation_time, 2),
            tokens_used=int(tokens_used),
            cost_estimate=round(cost_estimate, 4),
            search_results_used=bool(final_state.get("research_data")),
            citations=citations  # Include citations in response
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/tones")
async def get_available_tones():
    """Get available tone options"""
    return {
        "tones": [
            {"value": "professional", "label": "Professional"},
            {"value": "casual", "label": "Casual & Friendly"},
            {"value": "thought-leader", "label": "Thought Leadership"},
            {"value": "inspirational", "label": "Inspirational"},
            {"value": "educational", "label": "Educational"},
            {"value": "humorous", "label": "Light & Humorous"},
            {"value": "storytelling", "label": "Storytelling"}
        ]
    }

@app.get("/audiences")
async def get_available_audiences():
    """Get available audience options"""
    return {
        "audiences": [
            {"value": "general", "label": "General Professional"},
            {"value": "executives", "label": "Executives & Leaders"},
            {"value": "entrepreneurs", "label": "Entrepreneurs"},
            {"value": "tech-professionals", "label": "Tech Professionals"},
            {"value": "marketers", "label": "Marketing Professionals"},
            {"value": "students", "label": "Students & New Grads"},
            {"value": "consultants", "label": "Consultants"},
            {"value": "salespeople", "label": "Sales Professionals"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)