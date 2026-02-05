from crewai import Agent, Task, Crew
from typing import Dict, Any
import json
import re

class RoutingAgent:
    def __init__(self, llm, confidence_threshold: float = 0.7):
        self.llm = llm
        self.threshold = confidence_threshold
        self.agent = Agent(
            role="Document Routing Specialist",
            goal="Route documents based on quality metrics",
            backstory="""You are a routing expert who decides where documents 
            should go based on confidence levels and validation results.""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )
    
    def route(self, classification: Dict, extraction: Dict, validation: Dict) -> Dict[str, Any]:
        task = Task(
            description=f"""Route this document:

Classification confidence: {classification.get('confidence', 0)}
Extraction confidence: {extraction.get('confidence', 0)}
Validation: {validation.get('is_valid', False)}
Threshold: {self.threshold}

Rules:
- >0.8 confidence + valid → high_confidence_queue
- 0.5-0.8 → manual_review_queue
- <0.5 or invalid → specialist_review_queue

Return VALID JSON:
{{
    "destination": "queue_name",
    "reasoning": "explain decision",
    "confidence": 0.0 to 1.0,
    "requires_human_review": true or false
}}

ONLY JSON.""",
            agent=self.agent,
            expected_output="JSON routing decision"
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=False
        )
        
        try:
            result = crew.kickoff()
            result_str = str(result)
            
            json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
            else:
                raise ValueError("No JSON in response")
                
        except Exception as e:
            print(f"Routing error: {e}")
            return {
                "destination": "manual_review_queue",
                "reasoning": f"Error: {str(e)}",
                "confidence": 0.0,
                "requires_human_review": True
            }