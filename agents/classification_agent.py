from crewai import Agent, Task, Crew
from typing import Dict, Any
import json
import re

class ClassificationAgent:
    def __init__(self, llm):
        self.llm = llm
        # Pass llm explicitly and set allow_delegation=False
        self.agent = Agent(
            role="Document Classification Specialist",
            goal="Accurately identify document types with high confidence",
            backstory="""You are an expert document analyst who can identify 
            invoices, contracts, purchase orders, and technical specifications. 
            You analyze structure, terminology, and content to classify documents.""",
            verbose=False,
            allow_delegation=False,
            llm=llm  # Pass the LLM explicitly
        )
    
    def classify(self, document_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        # Truncate content for efficiency
        content_preview = document_content[:2000]
        
        task = Task(
            description=f"""Analyze this document and classify it.

Document Content:
{content_preview}

File Info: {metadata.get('file_size', 'unknown')} bytes

Identify the document type from these options:
- invoice: Has invoice number, items, prices, totals
- contract: Has parties, terms, obligations, signatures
- purchase_order: Has PO number, vendor, items to purchase
- technical_specification: Has product specs, requirements
- mixed: Contains multiple document types
- unknown: Cannot determine type

Provide your analysis as VALID JSON with this exact structure:
{{
    "document_type": "one of the types above",
    "confidence": 0.0 to 1.0,
    "reasoning": "explain your classification",
    "alternative_types": []
}}

IMPORTANT: Return ONLY the JSON object, no other text.""",
            agent=self.agent,
            expected_output="JSON classification result"
        )
        
        # Create crew with single agent and task
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=False
        )
        
        try:
            result = crew.kickoff()
            result_str = str(result)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Classification error: {e}")
            return {
                "document_type": "unknown",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
                "alternative_types": []
            }