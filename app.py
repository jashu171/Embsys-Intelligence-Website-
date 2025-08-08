"""
Working Unified Flask Application - Embsys Intelligence with Integrated Chatbot
Fixes: File uploads, LLM responses, and ChromaDB storage
"""

import os
import sys
import logging
import time
from datetime import datetime
from werkzeug.utils import secure_filename

# Load environment variables first
from dotenv import load_dotenv

load_dotenv()

# Flask imports
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS

# Add chatbot modules to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "chatbot_modules"))

# Import chatbot components with proper error handling
try:
    from chatbot_modules.utils.simple_vector_store import (
        SimpleVectorStore as VectorStore,
    )

    VECTOR_STORE_AVAILABLE = True
    print("✅ ChromaDB Vector Store loaded")
except ImportError as e:
    print(f"⚠️  ChromaDB Vector store not available: {e}")
    VECTOR_STORE_AVAILABLE = False

try:
    from chatbot_modules.utils.document_parser import DocumentParser

    DOCUMENT_PARSER_AVAILABLE = True
    print("✅ Document Parser loaded")
except ImportError as e:
    print(f"⚠️  Document Parser not available: {e}")
    DOCUMENT_PARSER_AVAILABLE = False

# Try to import Google Generative AI
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
    print("✅ Google Generative AI available")
except ImportError:
    GENAI_AVAILABLE = False
    print(
        "⚠️  Google Generative AI not available - install with: pip install google-generativeai"
    )


# Configuration
class Config:
    def __init__(self):
        self.upload_folder = "uploads"
        self.max_file_size_mb = 32
        self.allowed_extensions = {"pdf", "docx", "pptx", "csv", "txt", "md"}
        self.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
        self.debug_mode = True
        self.api_host = "0.0.0.0"
        self.api_port = 4000

        # Vector store config
        self.collection_name = "document_store"
        self.persist_directory = "./chroma_db"
        self.embedding_model = "all-MiniLM-L6-v2"

        # LLM config
        self.model_name = "gemini-2.0-flash-exp"
        self.max_tokens = 2048
        self.temperature = 0.7

        # Document processing
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.default_search_k = 5
        self.similarity_threshold = 0.0


config = Config()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("working_app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Flask configuration
app.config.update(
    {
        "UPLOAD_FOLDER": config.upload_folder,
        "MAX_CONTENT_LENGTH": config.max_file_size_mb * 1024 * 1024,
        "SECRET_KEY": config.secret_key,
        "DEBUG": config.debug_mode,
    }
)

# Create uploads directory
os.makedirs(config.upload_folder, exist_ok=True)

# Initialize components
vector_store = None
llm_model = None
document_parser = None

# Initialize vector store
vector_store = None
if VECTOR_STORE_AVAILABLE:
    try:
        vector_store = VectorStore(
            collection_name=config.collection_name,
            persist_directory=config.persist_directory,
        )
        logger.info("Vector store initialized successfully")

        # Test the vector store
        test_info = vector_store.get_collection_info()
        if test_info["status"] == "success":
            logger.info(
                f"Vector store ready - Collection: {test_info['collection_name']}, Documents: {test_info['document_count']}"
            )
        else:
            logger.warning(f"Vector store test failed: {test_info.get('error')}")

    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}")
        vector_store = None
        VECTOR_STORE_AVAILABLE = False

# Initialize LLM
if GENAI_AVAILABLE:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            llm_model = genai.GenerativeModel(config.model_name)
            logger.info(f"LLM model initialized: {config.model_name}")
        else:
            logger.warning("GEMINI_API_KEY not found in environment")
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {str(e)}")

# Initialize document parser
document_parser = None
if DOCUMENT_PARSER_AVAILABLE:
    try:
        document_parser = DocumentParser()
        logger.info("Document parser initialized")
    except Exception as e:
        logger.warning(f"Document parser initialization failed: {str(e)}")
        document_parser = None


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.allowed_extensions
    )


# Error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify(
        {"error": f"File too large. Maximum size is {config.max_file_size_mb}MB."}
    ), 413


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error occurred"}), 500


# ============================================================================
# COMPANY WEBSITE ROUTES
# ============================================================================


@app.route("/")
def index():
    """Company homepage"""
    return render_template("company/index.html")


@app.route("/about")
def about():
    """About page"""
    return render_template("company/about.html")


@app.route("/services")
def services():
    """Services page"""
    return render_template("company/services.html")


@app.route("/pricing")
def pricing():
    """Pricing page"""
    return render_template("company/pricing.html")


@app.route("/contact")
def contact():
    """Contact page"""
    return render_template("company/contact.html")


@app.route("/chat")
def chat():
    """Chatbot interface"""
    return render_template("chatbot/index.html")


@app.route("/start-free")
def start_free():
    """Handle the 'Start for Free' button click"""
    return redirect(url_for("chat"))


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("icon.png")


# ============================================================================
# CHATBOT API ROUTES
# ============================================================================


@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check endpoint"""
    try:
        collection_info = {}
        if vector_store:
            collection_info = vector_store.get_collection_info()

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "system_health": {
                    "vector_store_available": VECTOR_STORE_AVAILABLE,
                    "llm_available": GENAI_AVAILABLE and llm_model is not None,
                    "document_parser_available": document_parser is not None,
                    "collection_info": collection_info,
                },
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 503


@app.route("/api/upload", methods=["POST"])
def upload_files():
    """File upload endpoint with proper processing"""
    try:
        if "files" not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist("files")
        if not files or all(f.filename == "" for f in files):
            return jsonify({"error": "No files selected"}), 400

        results = {"uploaded_files": [], "failed_files": [], "processing_results": []}

        for file in files:
            if not file or file.filename == "":
                continue

            filename = secure_filename(file.filename)
            if not filename:
                results["failed_files"].append(
                    {"filename": file.filename, "error": "Invalid filename"}
                )
                continue

            if not allowed_file(filename):
                results["failed_files"].append(
                    {
                        "filename": filename,
                        "error": f"Unsupported file type. Allowed: {', '.join(config.allowed_extensions)}",
                    }
                )
                continue

            try:
                # Save file
                filepath = os.path.join(config.upload_folder, filename)
                file.save(filepath)
                logger.info(f"File saved: {filepath}")

                # Process document if components are available
                if vector_store and document_parser:
                    start_time = time.time()

                    # Parse document
                    parse_result = document_parser.parse_document(filepath)
                    if parse_result["status"] == "error":
                        results["failed_files"].append(
                            {
                                "filename": filename,
                                "error": f"Failed to parse document: {parse_result['error']}",
                            }
                        )
                        os.remove(filepath)
                        continue

                    # Chunk the text
                    text_content = parse_result["content"]
                    chunks = chunk_text(
                        text_content, config.chunk_size, config.chunk_overlap
                    )

                    # Create metadata for chunks
                    metadatas = []
                    for i, chunk in enumerate(chunks):
                        metadatas.append(
                            {
                                "source": filename,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                                "file_path": filepath,
                                "upload_time": datetime.now().isoformat(),
                            }
                        )

                    # Add to vector store
                    store_result = vector_store.add_documents(
                        texts=chunks, metadatas=metadatas
                    )

                    processing_time = time.time() - start_time

                    if store_result["status"] == "error":
                        results["failed_files"].append(
                            {
                                "filename": filename,
                                "error": f"Failed to store in vector database: {store_result['error']}",
                            }
                        )
                        os.remove(filepath)
                        continue

                    results["uploaded_files"].append(filename)
                    results["processing_results"].append(
                        {
                            "filename": filename,
                            "status": "processed",
                            "chunks_created": len(chunks),
                            "processing_time": round(processing_time, 2),
                            "collection_size": store_result.get("collection_size", 0),
                        }
                    )

                    logger.info(
                        f"Successfully processed {filename}: {len(chunks)} chunks"
                    )

                else:
                    # Just save the file without processing
                    results["uploaded_files"].append(filename)
                    results["processing_results"].append(
                        {
                            "filename": filename,
                            "status": "uploaded_only",
                            "message": "File saved but not processed (vector store not available)",
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                results["failed_files"].append(
                    {"filename": filename, "error": f"Processing error: {str(e)}"}
                )
                # Clean up file if it was saved
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except:
                    pass

        success_count = len(results["uploaded_files"])
        failed_count = len(results["failed_files"])

        if success_count == 0 and failed_count > 0:
            return jsonify(
                {**results, "message": f"All {failed_count} files failed to process"}
            ), 400
        elif failed_count > 0:
            return jsonify(
                {
                    **results,
                    "message": f"Processed {success_count} files, {failed_count} failed",
                }
            ), 207
        else:
            return jsonify(
                {**results, "message": f"Successfully processed {success_count} files"}
            )

    except Exception as e:
        logger.error(f"Upload endpoint error: {str(e)}")
        return jsonify({"error": "Upload failed", "details": str(e)}), 500


@app.route("/api/query", methods=["POST"])
def query():
    """Query processing endpoint with proper LLM integration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        query_text = data.get("query", "").strip()
        if not query_text:
            return jsonify({"error": "No query provided"}), 400

        search_k = data.get("search_k", config.default_search_k)
        search_k = max(1, min(search_k, 20))

        start_time = time.time()

        # Search for relevant context
        context_chunks = []
        chunk_metadata = []
        collection_size = 0

        if vector_store:
            logger.info(f"Searching vector store for query: '{query_text[:50]}...'")

            # First check collection status
            collection_info = vector_store.get_collection_info()
            if collection_info["status"] == "success":
                collection_size = collection_info["document_count"]
                logger.info(f"Collection has {collection_size} documents")
            else:
                logger.error(f"Collection info error: {collection_info.get('error')}")

            if collection_size > 0:
                search_result = vector_store.search(
                    query=query_text,
                    k=search_k,
                    similarity_threshold=config.similarity_threshold,
                )

                if search_result["status"] == "success":
                    context_chunks = search_result.get("top_chunks", [])
                    chunk_metadata = search_result.get("chunk_metadata", [])
                    similarity_scores = search_result.get("similarity_scores", [])
                    logger.info(
                        f"Found {len(context_chunks)} relevant chunks with scores: {similarity_scores[:3] if similarity_scores else 'N/A'}"
                    )

                    # Debug: Log all similarity scores to understand the threshold issue
                    if similarity_scores:
                        logger.info(f"All similarity scores: {similarity_scores}")
                        logger.info(f"Max similarity score: {max(similarity_scores)}")
                        logger.info(f"Min similarity score: {min(similarity_scores)}")

                else:
                    logger.warning(f"Search failed: {search_result.get('error')}")
            else:
                logger.warning(
                    "No documents in collection - upload some documents first"
                )
        else:
            logger.warning("Vector store not available")

        # Generate response
        answer = generate_response(query_text, context_chunks, chunk_metadata)

        processing_time = time.time() - start_time

        return jsonify(
            {
                "answer": answer,
                "context_chunks": context_chunks[:3],  # Return first 3 for display
                "sources_used": len(context_chunks),
                "collection_size": collection_size,
                "processing_time": round(processing_time, 2),
                "metadata": {
                    "query_length": len(query_text),
                    "search_k": search_k,
                    "timestamp": datetime.now().isoformat(),
                    "llm_available": llm_model is not None,
                    "vector_store_available": vector_store is not None,
                },
            }
        )

    except Exception as e:
        logger.error(f"Query processing error: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to process query", "details": str(e)}), 500


@app.route("/api/clear", methods=["POST"])
def clear_documents():
    """Clear all documents from the vector store"""
    try:
        if vector_store:
            clear_result = vector_store.clear_collection()
            if clear_result["status"] == "error":
                return jsonify({"error": clear_result["error"]}), 500

        # Clear uploaded files
        for filename in os.listdir(config.upload_folder):
            file_path = os.path.join(config.upload_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        logger.info("Document store and uploads cleared")

        return jsonify(
            {
                "message": "All documents cleared successfully",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        return jsonify({"error": "Failed to clear documents", "details": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """System statistics endpoint"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "system_status": {
                "vector_store_available": vector_store is not None,
                "llm_available": llm_model is not None,
                "document_parser_available": document_parser is not None,
            },
        }

        if vector_store:
            collection_info = vector_store.get_collection_info()
            stats["collection_info"] = collection_info

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({"error": "Failed to get statistics"}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """Split text into overlapping chunks"""
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # If this is not the last chunk, try to break at a sentence or word boundary
        if end < text_length:
            # Look for sentence boundary
            sentence_end = text.rfind(".", start, end)
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1
            else:
                # Look for word boundary
                word_end = text.rfind(" ", start, end)
                if word_end > start + chunk_size // 2:
                    end = word_end

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap
        if start >= text_length:
            break

    return chunks


def generate_response(query, context_chunks, chunk_metadata):
    """Generate response using available LLM or fallback"""
    try:
        logger.info(f"Generating response for query: '{query[:50]}...'")
        logger.info(f"Context chunks available: {len(context_chunks)}")
        logger.info(f"LLM model available: {llm_model is not None}")

        if llm_model and context_chunks:
            # Use LLM with context
            context_text = "\n\n".join(
                [
                    f"Context {i + 1}: {chunk}"
                    for i, chunk in enumerate(context_chunks[:5])
                ]
            )

            prompt = f"""Based on the following context from uploaded documents, please answer the user's question.

Context:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, please say so and provide what information you can from the context.

Important: Even if the similarity scores are low, if the context contains relevant information, please use it to answer the question."""

            logger.info("Sending request to LLM with context")
            response = llm_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=config.max_tokens,
                    temperature=config.temperature,
                ),
            )

            if response.text:
                logger.info("LLM response generated successfully")
                return response.text.strip()

        elif llm_model:
            # Use LLM without context
            prompt = f"""The user asked: {query}

No relevant documents were found in the knowledge base. Please provide a helpful general response and suggest that the user upload relevant documents for more specific information."""

            logger.info("Sending request to LLM without context")
            response = llm_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=config.max_tokens,
                    temperature=config.temperature,
                ),
            )

            if response.text:
                logger.info("LLM response generated successfully")
                return response.text.strip()

        # Fallback responses
        if context_chunks:
            logger.info("Using fallback response with context")
            return f"""Based on the uploaded documents, I found relevant information about your query: "{query}". 

Here's what I found:
{context_chunks[0][:500]}...

However, the AI model is not fully configured. Please set your GEMINI_API_KEY environment variable for more intelligent responses."""
        else:
            logger.info("Using fallback response without context")
            return f"""I received your query: "{query}". 

Currently, no relevant documents were found in the knowledge base, and the AI model is not fully configured. 

To get better responses:
1. Upload relevant documents using the attachment button
2. Set your GEMINI_API_KEY environment variable
3. Install required dependencies: pip install google-generativeai

I'm still learning and improving! Please try uploading some documents first."""

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return f"I encountered an error while processing your query: '{query}'. Please try again or check the system logs for more details."


if __name__ == "__main__":
    print("\n🚀 Working Embsys Intelligence Application")
    print("=" * 50)

    # System status
    status_items = []
    if vector_store:
        status_items.append("✅ ChromaDB Vector Store")
    else:
        status_items.append("❌ ChromaDB Vector Store")

    if llm_model:
        status_items.append("✅ Google Gemini LLM")
    else:
        status_items.append("❌ Google Gemini LLM (set GEMINI_API_KEY)")

    if document_parser:
        status_items.append("✅ Document Parser")
    else:
        status_items.append("❌ Document Parser")

    for item in status_items:
        print(item)

    print(f"\n🌍 Company Website: http://localhost:{config.api_port}")
    print(f"🤖 AI Chatbot: http://localhost:{config.api_port}/chat")
    print("=" * 50)

    app.run(debug=config.debug_mode, port=config.api_port, host=config.api_host)
