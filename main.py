"""
main.py - FastAPI Application for Document Processing
This is the main entry point for the application
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
import json
import aiofiles
from datetime import datetime
from typing import Dict
import uuid

from config import settings
from models import (
    DocumentUploadResponse, ProcessingResult, ProcessingStatus,
    ClassificationResult, ExtractionResult, ValidationResult, RoutingDecision
)
from workflow.document_workflow import DocumentWorkflow
from workflow.state import DocumentState
from agents.classification_agent import ClassificationAgent
from agents.extraction_agent import ExtractionAgent
from agents.validation_agent import ValidationAgent
from agents.routing_agent import RoutingAgent

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for processing results
processing_results: Dict[str, Dict] = {}
processing_queue: Dict[str, bool] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.state_dir, exist_ok=True)
    logger.info("=" * 60)
    logger.info("🚀 Document Processing System Starting...")
    logger.info("=" * 60)
    logger.info(f"📁 Upload directory: {settings.upload_dir}")
    logger.info(f"💾 State directory: {settings.state_dir}")
    logger.info(f"🤖 Using: {settings.llm_provider.upper()} ({settings.ollama_model})")
    logger.info(f"💰 Cost: $0 - FREE & LOCAL!")
    logger.info("=" * 60)
    yield
    # Shutdown
    logger.info("👋 Application shutting down...")

app = FastAPI(
    title="Document Processing System",
    description="AI-powered document processing with Ollama (FREE & LOCAL!)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM for CrewAI - OLLAMA
logger.info(f"🤖 Initializing {settings.llm_provider.upper()} for CrewAI...")

# Configure environment for Ollama with CrewAI
# CrewAI requires OPENAI_API_KEY even when using Ollama (it won't be used)
os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-crewai-compatibility"
logger.info("🔑 Set dummy OpenAI key for CrewAI compatibility")

try:
    # Use string format that CrewAI natively understands for Ollama
    # Format: "ollama/model_name" (without :latest tag)
    model_name = settings.ollama_model.replace(":latest", "")
    llm = f"ollama/{model_name}"
    
    logger.info(f"📡 Ollama endpoint: {settings.ollama_base_url}")
    logger.info(f"🎯 Using model: {llm}")
    logger.info(f"✅ Ollama configured for CrewAI!")
    logger.info(f"💰 Cost: $0 - Running locally, no API fees!")
    
except Exception as e:
    logger.error(f"❌ Failed to configure Ollama: {e}")
    logger.error("=" * 60)
    logger.error("📋 Troubleshooting Steps:")
    logger.error("1. Is Ollama running? → ollama serve")
    logger.error("2. Is model downloaded? → ollama list")
    logger.error("3. Verify connection: → curl http://localhost:11434/api/tags")
    logger.error("=" * 60)
    raise

# Initialize agents
logger.info("🔧 Initializing AI agents...")
try:
    classification_agent = ClassificationAgent(llm)
    extraction_agent = ExtractionAgent(llm)
    validation_agent = ValidationAgent(llm)
    routing_agent = RoutingAgent(llm, settings.confidence_threshold)
    logger.info("✅ All agents initialized!")
except Exception as e:
    logger.error(f"❌ Failed to initialize agents: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise

# Initialize workflow
logger.info("🔄 Building workflow graph...")
try:
    workflow = DocumentWorkflow(
        classification_agent, 
        extraction_agent, 
        validation_agent, 
        routing_agent
    )
    logger.info("✅ Workflow ready!")
except Exception as e:
    logger.error(f"❌ Failed to build workflow: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise

logger.info("=" * 60)

async def process_document_background(document_id: str, filepath: str, filename: str):
    """Background task to process document through the workflow"""
    try:
        # Update status to processing
        processing_results[document_id]["status"] = ProcessingStatus.PROCESSING
        logger.info(f"📄 Starting processing: {filename} (ID: {document_id})")
        
        # Read document content
        async with aiofiles.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        
        logger.info(f"📖 Read {len(content)} characters from {filename}")
        
        # Create initial state
        state: DocumentState = {
            "document_id": document_id,
            "filename": filename,
            "content": content,
            "metadata": {
                "upload_time": datetime.utcnow().isoformat(),
                "file_size": os.path.getsize(filepath),
                "filepath": filepath
            },
            "status": "pending",
            "classification_result": None,
            "extraction_result": None,
            "validation_result": None,
            "routing_decision": None,
            "errors": [],
            "start_time": datetime.utcnow(),
            "end_time": None
        }
        
        # Process through workflow
        logger.info(f"🔄 Running workflow for {document_id}...")
        result_state = await workflow.process_document(state)
        
        # Calculate processing time
        processing_time = None
        if result_state.get('end_time'):
            delta = result_state['end_time'] - result_state['start_time']
            processing_time = delta.total_seconds()
            logger.info(f"⏱️  Processing completed in {processing_time:.1f}s")
        
        # Build final result
        final_result = ProcessingResult(
            document_id=document_id,
            status=ProcessingStatus(result_state['status']),
            classification=ClassificationResult(**result_state['classification_result']) if result_state.get('classification_result') else None,
            extraction=ExtractionResult(**result_state['extraction_result']) if result_state.get('extraction_result') else None,
            validation=ValidationResult(**result_state['validation_result']) if result_state.get('validation_result') else None,
            routing=RoutingDecision(**result_state['routing_decision']) if result_state.get('routing_decision') else None,
            processing_time=processing_time,
            errors=result_state['errors']
        )
        
        # Store result in memory
        processing_results[document_id] = json.loads(final_result.model_dump_json())
        
        # Save result to disk
        result_path = os.path.join(settings.state_dir, f"{document_id}.json")
        async with aiofiles.open(result_path, 'w') as f:
            await f.write(final_result.model_dump_json(indent=2))
        
        logger.info(f"✅ Successfully processed: {filename}")
        logger.info(f"📊 Classification: {result_state['classification_result'].get('document_type', 'unknown')}")
        logger.info(f"🎯 Routing: {result_state['routing_decision'].get('destination', 'unknown')}")
        
    except Exception as e:
        logger.error(f"❌ Error processing document {document_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        processing_results[document_id] = {
            "document_id": document_id,
            "status": ProcessingStatus.FAILED,
            "errors": [str(e)],
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        processing_queue[document_id] = False

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Document Processing System",
        "version": "1.0.0",
        "llm": f"{settings.llm_provider.upper()} ({settings.ollama_model}) - FREE & LOCAL!",
        "endpoints": {
            "upload": "/api/v1/documents/upload",
            "status": "/api/v1/documents/{document_id}/status",
            "results": "/api/v1/documents/{document_id}/results",
            "list": "/api/v1/documents",
            "docs": "/docs"
        }
    }

@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a document for processing
    
    Accepts: .txt, .pdf, .doc, .docx files
    Returns: Document ID and status
    """
    try:
        logger.info(f"📤 Received upload request: {file.filename}")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.doc', '.docx']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            logger.warning(f"❌ Invalid file type: {file_ext}")
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_ext}' not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check concurrent processing limit
        active_processing = sum(1 for v in processing_queue.values() if v)
        if active_processing >= settings.max_concurrent_requests:
            logger.warning(f"⚠️  Too many concurrent requests: {active_processing}/{settings.max_concurrent_requests}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many concurrent requests ({active_processing}/{settings.max_concurrent_requests}). Please try again later."
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save uploaded file
        filepath = os.path.join(settings.upload_dir, f"{document_id}_{file.filename}")
        async with aiofiles.open(filepath, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"💾 Saved file: {filepath} ({len(content)} bytes)")
        
        # Initialize result storage
        processing_results[document_id] = {
            "document_id": document_id,
            "status": ProcessingStatus.PENDING,
            "filename": file.filename,
            "timestamp": datetime.utcnow().isoformat()
        }
        processing_queue[document_id] = True
        
        # Add to background processing queue
        background_tasks.add_task(
            process_document_background,
            document_id,
            filepath,
            file.filename
        )
        
        logger.info(f"✅ Document queued for processing: {document_id}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            status=ProcessingStatus.PENDING,
            message=f"Document '{file.filename}' uploaded successfully and queued for processing with FREE Ollama (Local AI)!"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(document_id: str):
    """Get current processing status of a document"""
    if document_id not in processing_results:
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = processing_results[document_id]
    return {
        "document_id": document_id,
        "status": result.get("status"),
        "filename": result.get("filename"),
        "timestamp": result.get("timestamp")
    }

@app.get("/api/v1/documents/{document_id}/results")
async def get_document_results(document_id: str):
    """Get complete processing results for a document"""
    if document_id not in processing_results:
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = processing_results[document_id]
    
    if result.get("status") == ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=202,
            detail="Document is still pending processing. Please check status endpoint."
        )
    
    if result.get("status") == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=202,
            detail="Document is currently being processed. Please try again in a few moments."
        )
    
    return ProcessingResult(**result)

@app.delete("/api/v1/documents/{document_id}")
async def cancel_processing(document_id: str):
    """Cancel document processing (only if still pending)"""
    if document_id not in processing_results:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if processing_results[document_id].get("status") == ProcessingStatus.PENDING:
        processing_results[document_id]["status"] = ProcessingStatus.FAILED
        processing_results[document_id]["errors"] = ["Processing cancelled by user"]
        processing_queue[document_id] = False
        
        logger.info(f"🚫 Processing cancelled for document: {document_id}")
        return {"message": "Processing cancelled successfully"}
    else:
        current_status = processing_results[document_id].get("status")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel: document is already '{current_status}'"
        )

@app.get("/api/v1/documents")
async def list_documents():
    """List all documents and their current status"""
    return {
        "documents": [
            {
                "document_id": doc_id,
                "status": result.get("status"),
                "filename": result.get("filename"),
                "timestamp": result.get("timestamp")
            }
            for doc_id, result in processing_results.items()
        ],
        "total": len(processing_results),
        "processing": sum(1 for r in processing_results.values() if r.get("status") == ProcessingStatus.PROCESSING),
        "completed": sum(1 for r in processing_results.values() if r.get("status") == ProcessingStatus.COMPLETED)
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"🚨 Unhandled exception: {str(exc)}")
    import traceback
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting Document Processing System")
    print("=" * 60)
    print(f"📡 Server will run on: http://{settings.app_host}:{settings.app_port}")
    print(f"📚 API Documentation: http://{settings.app_host}:{settings.app_port}/docs")
    print(f"🤖 LLM: {settings.llm_provider.upper()} ({settings.ollama_model})")
    print(f"💰 Cost: $0 - FREE & LOCAL!")
    print(f"🔗 Ollama: {settings.ollama_base_url}")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )