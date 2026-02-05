from langgraph.graph import StateGraph, END
from workflow.state import DocumentState
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DocumentWorkflow:
    def __init__(self, classification_agent, extraction_agent, 
                 validation_agent, routing_agent):
        self.classification_agent = classification_agent
        self.extraction_agent = extraction_agent
        self.validation_agent = validation_agent
        self.routing_agent = routing_agent
        self.graph = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(DocumentState)
        
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("extract", self._extract_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("route", self._route_node)
        
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "extract")
        workflow.add_edge("extract", "validate")
        workflow.add_edge("validate", "route")
        workflow.add_edge("route", END)
        
        return workflow.compile()
    
    def _classify_node(self, state: DocumentState) -> DocumentState:
        try:
            logger.info(f"Classifying {state['document_id']}")
            result = self.classification_agent.classify(
                state['content'], state['metadata']
            )
            state['classification_result'] = result
            state['status'] = 'classified'
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            state['errors'].append(f"Classification: {e}")
            state['classification_result'] = {
                "document_type": "unknown",
                "confidence": 0.0,
                "reasoning": str(e)
            }
        return state
    
    def _extract_node(self, state: DocumentState) -> DocumentState:
        try:
            logger.info(f"Extracting {state['document_id']}")
            doc_type = state['classification_result'].get('document_type', 'unknown')
            result = self.extraction_agent.extract(state['content'], doc_type)
            state['extraction_result'] = result
            state['status'] = 'extracted'
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            state['errors'].append(f"Extraction: {e}")
            state['extraction_result'] = {
                "fields": {},
                "confidence": 0.0,
                "extraction_method": "failed",
                "warnings": [str(e)]
            }
        return state
    
    def _validate_node(self, state: DocumentState) -> DocumentState:
        try:
            logger.info(f"Validating {state['document_id']}")
            result = self.validation_agent.validate(
                state['extraction_result'], state['content']
            )
            state['validation_result'] = result
            state['status'] = 'validated'
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            state['errors'].append(f"Validation: {e}")
            state['validation_result'] = {
                "is_valid": False,
                "conflicts": [],
                "missing_fields": [],
                "confidence": 0.0,
                "warnings": [str(e)]
            }
        return state
    
    def _route_node(self, state: DocumentState) -> DocumentState:
        try:
            logger.info(f"Routing {state['document_id']}")
            result = self.routing_agent.route(
                state['classification_result'],
                state['extraction_result'],
                state['validation_result']
            )
            state['routing_decision'] = result
            state['status'] = 'completed'
            state['end_time'] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            state['errors'].append(f"Routing: {e}")
            state['routing_decision'] = {
                "destination": "manual_review_queue",
                "reasoning": str(e),
                "confidence": 0.0,
                "requires_human_review": True
            }
            state['status'] = 'partial'
        return state
    
    async def process_document(self, state: DocumentState) -> DocumentState:
        try:
            result = await self.graph.ainvoke(state)
            return result
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            state['errors'].append(f"Workflow: {e}")
            state['status'] = 'failed'
            return state