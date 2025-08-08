"""
Test RAG Pipeline - Document Upload, Storage, and Retrieval
"""

import os
import sys
import logging
from datetime import datetime

# Add chatbot modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'chatbot_modules'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rag_pipeline():
    """Test the complete RAG pipeline"""
    
    print("🧪 Testing RAG Pipeline")
    print("=" * 50)
    
    # Test 1: Import components
    print("\n1. Testing imports...")
    try:
        from chatbot_modules.utils.simple_vector_store import SimpleVectorStore
        from chatbot_modules.utils.document_parser import DocumentParser
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Initialize components
    print("\n2. Initializing components...")
    try:
        vector_store = SimpleVectorStore(
            collection_name="test_collection",
            persist_directory="./test_chroma_db"
        )
        document_parser = DocumentParser()
        print("✅ Components initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test 3: Create test document
    print("\n3. Creating test document...")
    test_content = """
    Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines.
    Machine Learning is a subset of AI that enables computers to learn without being explicitly programmed.
    Deep Learning is a subset of machine learning that uses neural networks with multiple layers.
    Natural Language Processing (NLP) helps computers understand and process human language.
    Computer Vision enables machines to interpret and understand visual information from the world.
    """
    
    test_file_path = "test_document.txt"
    try:
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        print("✅ Test document created")
    except Exception as e:
        print(f"❌ Document creation failed: {e}")
        return False
    
    # Test 4: Parse document
    print("\n4. Testing document parsing...")
    try:
        parse_result = document_parser.parse_document(test_file_path)
        if parse_result["status"] == "success":
            print(f"✅ Document parsed successfully")
            print(f"   Content length: {len(parse_result['content'])} characters")
        else:
            print(f"❌ Document parsing failed: {parse_result['error']}")
            return False
    except Exception as e:
        print(f"❌ Document parsing error: {e}")
        return False
    
    # Test 5: Chunk text
    print("\n5. Testing text chunking...")
    try:
        def chunk_text(text, chunk_size=200, chunk_overlap=50):
            chunks = []
            start = 0
            text_length = len(text)
            
            while start < text_length:
                end = start + chunk_size
                if end < text_length:
                    # Look for sentence boundary
                    sentence_end = text.rfind('.', start, end)
                    if sentence_end > start + chunk_size // 2:
                        end = sentence_end + 1
                
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                
                start = end - chunk_overlap
                if start >= text_length:
                    break
            
            return chunks
        
        chunks = chunk_text(parse_result["content"])
        print(f"✅ Text chunked into {len(chunks)} pieces")
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}: {chunk[:100]}...")
    except Exception as e:
        print(f"❌ Text chunking error: {e}")
        return False
    
    # Test 6: Store in vector database
    print("\n6. Testing vector storage...")
    try:
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadatas.append({
                "source": "test_document.txt",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "upload_time": datetime.now().isoformat()
            })
        
        store_result = vector_store.add_documents(
            texts=chunks,
            metadatas=metadatas
        )
        
        if store_result["status"] == "success":
            print(f"✅ Documents stored successfully")
            print(f"   Documents added: {store_result['documents_added']}")
            print(f"   Collection size: {store_result['collection_size']}")
        else:
            print(f"❌ Storage failed: {store_result['error']}")
            return False
    except Exception as e:
        print(f"❌ Vector storage error: {e}")
        return False
    
    # Test 7: Test retrieval
    print("\n7. Testing document retrieval...")
    test_queries = [
        "What is artificial intelligence?",
        "Tell me about machine learning",
        "What is deep learning?",
        "How does NLP work?",
        "What is computer vision?"
    ]
    
    for query in test_queries:
        try:
            search_result = vector_store.search(
                query=query,
                k=3,
                similarity_threshold=0.1
            )
            
            if search_result["status"] == "success":
                chunks_found = len(search_result["top_chunks"])
                print(f"✅ Query: '{query}'")
                print(f"   Found {chunks_found} relevant chunks")
                
                if chunks_found > 0:
                    best_chunk = search_result["top_chunks"][0]
                    similarity = search_result["similarity_scores"][0] if search_result["similarity_scores"] else "N/A"
                    print(f"   Best match (similarity: {similarity}): {best_chunk[:150]}...")
                else:
                    print("   No relevant chunks found")
            else:
                print(f"❌ Search failed for '{query}': {search_result['error']}")
                
        except Exception as e:
            print(f"❌ Retrieval error for '{query}': {e}")
    
    # Test 8: Test LLM integration (if available)
    print("\n8. Testing LLM integration...")
    try:
        import google.generativeai as genai
        import os
        
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            # Test query with context
            query = "What is the difference between AI and machine learning?"
            search_result = vector_store.search(query=query, k=2)
            
            if search_result["status"] == "success" and search_result["top_chunks"]:
                context = "\n\n".join(search_result["top_chunks"])
                
                prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided."""

                response = model.generate_content(prompt)
                
                if response.text:
                    print("✅ LLM integration working")
                    print(f"   Query: {query}")
                    print(f"   Context chunks used: {len(search_result['top_chunks'])}")
                    print(f"   Response: {response.text[:200]}...")
                else:
                    print("❌ LLM response empty")
            else:
                print("❌ No context found for LLM test")
        else:
            print("⚠️  GEMINI_API_KEY not set - skipping LLM test")
            
    except ImportError:
        print("⚠️  Google Generative AI not available - skipping LLM test")
    except Exception as e:
        print(f"❌ LLM integration error: {e}")
    
    # Test 9: Collection info
    print("\n9. Testing collection info...")
    try:
        info = vector_store.get_collection_info()
        if info["status"] == "success":
            print("✅ Collection info retrieved")
            print(f"   Collection: {info['collection_name']}")
            print(f"   Documents: {info['document_count']}")
            print(f"   Embedding model: {info['embedding_model']}")
        else:
            print(f"❌ Collection info failed: {info['error']}")
    except Exception as e:
        print(f"❌ Collection info error: {e}")
    
    # Cleanup
    print("\n10. Cleaning up...")
    try:
        # Remove test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        
        # Clear collection
        vector_store.clear_collection()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 RAG Pipeline Test Completed!")
    print("If you see mostly ✅ marks above, your RAG system is working correctly.")
    return True

if __name__ == "__main__":
    test_rag_pipeline()