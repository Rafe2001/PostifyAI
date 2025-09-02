from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import re 
from urllib.parse import urlparse
import ast
import json
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tools
@tool
def search_linkedin_trends(topic: str) -> Dict[str, Any]:
    """Search for current trends and popular content related to the topic on LinkedIn and web."""
    try:
        # Use DuckDuckGoSearchResults with JSON output to get URLs
        search = DuckDuckGoSearchResults(output_format="json")
        
        query = f"LinkedIn {topic} trending posts 2024 2025"
        results_json = search.run(query)
        
        # Parse the JSON results
        results = json.loads(results_json)
        
        # Extract citations
        citations = []
        research_text = f"Research findings for {topic}:\n\n"
        
        for i, result in enumerate(results):  
            title = result.get('title')
            link = result.get('link', '')
            snippet = result.get('snippet', '')
            
            citations.append({
                'title': title,
                'link': link,
                'snippet': snippet
            })
            
            research_text += f"{i+1}. {title}\n{snippet}\n\n"
        
        return {
            'research_text': research_text,
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


# @tool
# def post_image_generator()

# if __name__ == "__main__":
#     # Direct function calls
#     print(search_linkedin_trends("AI in healthcare"))
    # print(analyze_hashtag_performance("startup funding"))


 