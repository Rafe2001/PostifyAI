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
from agent import Agent, AgentState
from typing import TypedDict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        final_state = await Agent.ainvoke(initial_state)
        
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
    uvicorn.run(app, host="0.0.0.0", port=8500)