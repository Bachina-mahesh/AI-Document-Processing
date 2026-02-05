from crewai import Agent, Task, Crew
from typing import Dict, Any
import json
import re

class ValidationAgent:
    def __init__(self, llm):
        self.llm = llm
        self.agent = Agent(
            role="Data Validation Specialist",
            goal="Ensure data consistency and quality",
            backstory="""You are a quality assurance expert who validates 
            extracted data for consistency and completeness.""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )
    
    def validate(self, extracted_data: Dict[str, Any], document_content: str) -> Dict[str, Any]:
        content_preview = document_content[:1500]
        
        task = Task(
            description=f"""Validate this extracted data:

Extracted: {json.dumps(extracted_data.get('fields', {}), indent=2)}
Original: {content_preview}

Check:
1. Do values match the document?
2. Are there any conflicts?
3. Are critical fields missing?
4. Is data logically consistent?

Return VALID JSON:
{{
    "is_valid": true or false,
    "conflicts": ["list conflicts"],
    "missing_fields": ["list missing"],
    "confidence": 0.0 to 1.0,
    "warnings": ["list warnings"]
}}

ONLY return JSON.""",
            agent=self.agent,
            expected_output="JSON validation result"
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
            print(f"Validation error: {e}")
            return {
                "is_valid": False,
                "conflicts": [],
                "missing_fields": [],
                "confidence": 0.0,
                "warnings": [str(e)]
            }