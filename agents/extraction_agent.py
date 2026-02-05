from crewai import Agent, Task, Crew
from typing import Dict, Any
import json
import re

class ExtractionAgent:
    def __init__(self, llm):
        self.llm = llm
        self.agent = Agent(
            role="Data Extraction Specialist",
            goal="Extract accurate data from documents",
            backstory="""You are a data extraction expert who finds and extracts 
            relevant fields from documents, handling various formats and structures.""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )
    
    def extract(self, document_content: str, document_type: str) -> Dict[str, Any]:
        content_preview = document_content[:2500]
        
        field_templates = {
            "invoice": "invoice_number, date, vendor, total_amount, items, tax",
            "contract": "parties, effective_date, term, value, obligations",
            "purchase_order": "po_number, date, vendor, items, total, delivery_date",
            "technical_specification": "product_name, version, specifications",
        }
        
        fields = field_templates.get(document_type, "key_information")
        
        task = Task(
            description=f"""Extract data from this {document_type}:

Document:
{content_preview}

Extract these fields: {fields}

Return VALID JSON with this structure:
{{
    "fields": {{
        "field_name": "extracted_value",
        ...
    }},
    "confidence": 0.0 to 1.0,
    "extraction_method": "ai_extraction",
    "warnings": ["list any issues"]
}}

IMPORTANT: Return ONLY JSON, no other text.""",
            agent=self.agent,
            expected_output="JSON extraction result"
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
            print(f"Extraction error: {e}")
            return {
                "fields": {},
                "confidence": 0.0,
                "extraction_method": "failed",
                "warnings": [str(e)]
            }