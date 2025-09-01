from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

# Tools
@tool
def search_linkedin_trends(topic: str) -> str:
    """Search for current trends and popular content related to the topic on LinkedIn and web."""
    try:
        search = DuckDuckGoSearchRun()
        query = f"LinkedIn {topic} trending posts 2024 2025"
        results = search.run(query)
        return f"Research findings for {topic}: {results}"
    except Exception as e:
        return f"Search unavailable: {str(e)}"

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
#     #print(search_linkedin_trends("AI in healthcare"))
#     print(analyze_hashtag_performance("startup funding"))
