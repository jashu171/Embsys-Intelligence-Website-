# 🚀 N8N Webhook Integration - Quick Start

## What You Have Now

Your AI chatbot is **already equipped** with N8N webhook integration! Here's what's working:

✅ **Webhook UI**: Lightning bolt (⚡) button in chat interface  
✅ **Backend API**: `/api/webhook` endpoint ready to use  
✅ **Error Handling**: Comprehensive error management  
✅ **Response Formatting**: Beautiful JSON display  
✅ **Default URL**: Pre-configured for `http://localhost:5678/webhook-test/chicago`

## 🏃‍♂️ Quick Start (2 Minutes)

### Step 1: Start Your Apps
```bash
# Terminal 1: Start your Flask app
python app.py

# Terminal 2: Start N8N
npx n8n
```

### Step 2: Create N8N Webhook
1. Go to http://localhost:5678
2. Create new workflow
3. Add "Webhook" node:
   - Path: `webhook-test/chicago`
   - Method: `GET`
4. Add "Respond to Webhook" node
5. Connect them and activate workflow

### Step 3: Test It!
1. Go to http://localhost:4000/chat
2. Click the ⚡ webhook button
3. Click "Call Webhook"
4. See the magic happen! ✨

## 🎯 What Happens

```
Your Chat → Flask App → N8N Webhook → Your Workflow → Response → Chat Display
```

## 📁 Files Created

- `N8N_WEBHOOK_INTEGRATION_GUIDE.md` - Complete documentation
- `test_n8n_webhook.py` - Test script
- `setup_n8n_integration.py` - Setup helper
- `n8n_example_workflow.json` - Import this into N8N!

## 🔧 Quick Test

Run the test script to verify everything:
```bash
python test_n8n_webhook.py
```

## 🆘 Need Help?

1. **Flask not starting?** Check if port 4000 is free
2. **N8N not working?** Install with `npm install -g n8n`
3. **Webhook not responding?** Make sure N8N workflow is active
4. **Still stuck?** Check the full guide: `N8N_WEBHOOK_INTEGRATION_GUIDE.md`

## 🎉 You're Ready!

Your webhook integration is **complete and ready to use**. Start building amazing N8N workflows and watch your chatbot come alive with automation powers!

---
*Happy automating! 🤖⚡*





# Enhanced RAG Pipeline System

A comprehensive Retrieval-Augmented Generation (RAG) system with multi-format document processing, email alerts, and intelligent question-answering capabilities.

## Features

### 🚀 Core Capabilities
- **Multi-format Document Processing**: PDF, DOCX, PPTX, CSV, XLSX, TXT, MD
- **Intelligent Chunking**: Sentence-boundary aware text segmentation
- **Vector Storage**: ChromaDB with persistent storage
- **RAG + General Knowledge**: Hybrid response generation using Google Gemini 2.0 Flash
- **Email Alerts**: Automatic notifications for Excel files with contact information
- **Web Interface**: Clean, responsive chat interface

### 📧 Email Alert System
- **Contact Detection**: Automatically extracts emails, phone numbers, and locations from Excel files
- **Smart Notifications**: Sends alerts to detected email addresses
- **SMTP Support**: Configurable email server settings
- **Template System**: Professional HTML email templates

### 🔍 Advanced Search & Retrieval
- **Semantic Search**: Similarity-based document retrieval
- **Metadata Filtering**: Search within specific files or document types
- **Confidence Scoring**: Quality assessment of retrieved context
- **Source Attribution**: Clear references to original documents

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd enhanced-rag-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: GEMINI_API_KEY
# Optional: SMTP settings for email alerts
```

### 3. Run the Application

```bash
python app.py
```

Visit `http://localhost:8000` to access the web interface.

## Configuration

### Required Environment Variables

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Optional Configuration

#### Document Processing
```bash
CHUNK_SIZE=1000                    # Characters per chunk
CHUNK_OVERLAP=200                  # Overlap between chunks
```

#### Vector Storage
```bash
COLLECTION_NAME=rag_documents      # ChromaDB collection name
EMBEDDING_MODEL=all-MiniLM-L6-v2   # Sentence transformer model
PERSIST_DIRECTORY=./chroma_db      # Storage directory
```

#### Email Alerts
```bash
EMAIL_ALERTS_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
SMTP_SENDER_EMAIL=your_email@gmail.com
SMTP_SENDER_NAME=RAG Pipeline System
```

## API Endpoints

### Document Management

#### Upload Documents
```http
POST /upload
Content-Type: multipart/form-data

files: [file1, file2, ...]
enable_email_alerts: true/false (optional)
```

#### Query Documents
```http
POST /query
Content-Type: application/json

{
  "query": "Your question here",
  "search_k": 5,
  "file_filter": "optional_filename"
}
```

#### System Health
```http
GET /health
```

#### Document Statistics
```http
GET /documents/stats
```

#### Clear Documents
```http
DELETE /documents
```

### Email Configuration

#### Configure Email Settings
```http
POST /email/configure
Content-Type: application/json

{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your_email@gmail.com",
  "password": "your_password",
  "use_tls": true,
  "sender_email": "your_email@gmail.com",
  "sender_name": "RAG Pipeline System"
}
```

#### Test Email Configuration
```http
POST /email/test
```

## Architecture

### System Components

1. **Document Parser**: Multi-format document processing with contact detection
2. **Vector Store**: ChromaDB-based semantic search and storage
3. **LLM Generator**: Google Gemini 2.0 Flash integration for response generation
4. **Email Service**: SMTP-based notification system
5. **RAG Pipeline**: Main orchestration controller
6. **Web API**: Flask-based REST API with CORS support

### Data Flow

1. **Document Upload** → Parse → Extract Contacts → Store in Vector DB → Send Email Alerts
2. **Query Processing** → Semantic Search → Context Retrieval → LLM Generation → Response

## Supported File Formats

| Format | Extension | Features |
|--------|-----------|----------|
| PDF | .pdf | Page-aware chunking |
| Word | .docx | Section-aware processing |
| PowerPoint | .pptx | Slide-based organization |
| Excel | .xlsx | Contact detection, sheet processing |
| CSV | .csv | Column analysis, statistics |
| Text | .txt, .md | Encoding detection |

## Email Alert Features

### Contact Detection
- **Email Addresses**: RFC-compliant validation
- **Phone Numbers**: US and international formats
- **Locations**: Address pattern recognition

### Alert Types
- **Contact Discovery**: Notifications when contact info is found
- **Processing Complete**: Confirmation emails for successful uploads

### Template System
- **HTML Templates**: Professional email formatting
- **Dynamic Content**: File-specific information
- **Responsive Design**: Mobile-friendly emails

## Development

### Project Structure
```
enhanced-rag-pipeline/
├── app.py                 # Main Flask application
├── models/
│   └── data_models.py     # Data structures and configuration
├── services/
│   ├── document_parser.py # Document processing
│   ├── vector_store.py    # ChromaDB integration
│   ├── llm_response_generator.py # Gemini integration
│   └── email_alert_service.py # Email notifications
├── controllers/
│   └── rag_pipeline.py    # Main orchestration
├── static/                # Frontend assets
├── templates/             # HTML templates
└── requirements.txt       # Dependencies
```

### Adding New Document Formats

1. Extend `DocumentParser` class
2. Add format-specific extraction method
3. Update `get_supported_extensions()`
4. Add format to file upload validation

### Customizing Email Templates

1. Modify `create_alert_template()` in `EmailAlertService`
2. Update HTML structure and styling
3. Add new template variables as needed

## Troubleshooting

### Common Issues

#### "LLM model not available"
- Verify `GEMINI_API_KEY` is set correctly
- Check internet connectivity
- Ensure API key has proper permissions

#### "SMTP connection failed"
- Verify SMTP server settings
- Check firewall/network restrictions
- For Gmail: use App Passwords, not regular password

#### "ChromaDB initialization failed"
- Ensure write permissions for `PERSIST_DIRECTORY`
- Check disk space availability
- Verify sentence-transformers model download

### Logging

The system provides comprehensive logging:
- Application logs: `app.log`
- Component-specific logging levels
- Error tracking with stack traces

### Performance Optimization

- **Batch Processing**: Documents processed in configurable batches
- **Connection Pooling**: Efficient database connections
- **Caching**: Response caching for improved performance
- **Async Processing**: Non-blocking operations where possible

## Security Considerations

- **API Key Management**: Environment-based configuration
- **Input Validation**: Comprehensive request sanitization
- **File Upload Security**: Type and size restrictions
- **Email Security**: SMTP credential encryption
- **CORS Configuration**: Configurable cross-origin policies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Create an issue on GitHub
4. Contact the development team

---

**Enhanced RAG Pipeline** - Intelligent document processing with email alerts and advanced AI capabilities.
