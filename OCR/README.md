# FRA OCR Integration

This directory contains the OCR (Optical Character Recognition) integration for the FRA Atlas WebGIS system. It provides automated document processing capabilities for FRA claim forms using Tesseract OCR and Google's Gemini AI.

## Features

- **Document Upload**: Support for PDF, JPG, and PNG files
- **OCR Processing**: Text extraction using Tesseract OCR
- **AI-Powered Data Extraction**: Structured data extraction using Google Gemini
- **Confidence Scoring**: OCR confidence assessment
- **Human Verification**: Manual review and correction interface
- **Database Integration**: Automatic saving to SQLite database
- **REST API**: Flask-based API for frontend integration

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Tesseract OCR installed on your system
- Internet connection (for Gemini AI API)

### Tesseract OCR Installation

**Windows:**
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Download English language data

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

## Installation

1. **Navigate to the OCR directory:**
   ```bash
   cd OCR
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Gemini API key:**
   - Get your API key from Google AI Studio
   - Update the API key in `flask_ocr_api.py` (line 22)

## Usage

### Starting the OCR API Server

1. **Run the startup script:**
   ```bash
   python start_ocr_api.py
   ```

2. **Or run directly:**
   ```bash
   python flask_ocr_api.py
   ```

The API will be available at `http://localhost:5000`

### API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload-document` - Upload and process document
- `POST /api/save-claim` - Save extracted claim data
- `GET /api/claims` - Get all claims
- `GET /api/claim/<id>` - Get specific claim details
- `PUT /api/claim/<id>/status` - Update claim status

### Using the Web Interface

1. Open the FRA Claims Management page
2. Click "Upload Document" button
3. Drag and drop or browse for a document
4. Review the extracted data
5. Make corrections if needed
6. Save as a new claim

## File Structure

```
OCR/
├── flask_ocr_api.py          # Main Flask API server
├── start_ocr_api.py          # Startup script with checks
├── requirements.txt          # Python dependencies
├── fra_claims.db            # SQLite database (created automatically)
├── fra_extractor_app.py     # Original Streamlit app
├── ocr_app.py              # Simple OCR demo
├── gemini.py               # Gemini API test
└── README.md               # This file
```

## Configuration

### Tesseract Configuration
The system automatically detects Tesseract installation. For custom paths, modify the configuration in `flask_ocr_api.py`:

```python
# Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Linux/Mac (usually works with default PATH)
```

### Gemini API Configuration
Update the API key in `flask_ocr_api.py`:

```python
genai.configure(api_key="YOUR_API_KEY_HERE")
```

## Database Schema

The system uses SQLite with the following schema:

```sql
CREATE TABLE fra_claim_individual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_filename TEXT,
    claimant_name TEXT,
    spouse_name TEXT,
    father_or_mother_name TEXT,
    address TEXT,
    village TEXT,
    gram_panchayat TEXT,
    tehsil_taluka TEXT,
    district TEXT,
    state TEXT,
    is_scheduled_tribe TEXT,
    is_otfd TEXT,
    land_area TEXT,
    raw_text TEXT,
    ocr_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending_review'
);
```

## Troubleshooting

### Common Issues

1. **Tesseract not found:**
   - Ensure Tesseract is installed and in PATH
   - Check the configuration in `flask_ocr_api.py`

2. **Gemini API errors:**
   - Verify your API key is correct
   - Check your internet connection
   - Ensure you have API quota remaining

3. **PDF processing fails:**
   - Install poppler-utils: `sudo apt-get install poppler-utils` (Linux)
   - For Windows, download poppler and update the path

4. **Database errors:**
   - Check file permissions in the OCR directory
   - Ensure SQLite is working properly

### Debug Mode

Run with debug mode for detailed error messages:

```bash
python flask_ocr_api.py
```

## Integration with FRA Atlas

The OCR system integrates seamlessly with the FRA Atlas WebGIS:

1. **Frontend Integration**: The claims management page includes upload functionality
2. **Data Flow**: Documents → OCR → AI Extraction → Database → WebGIS Display
3. **Verification Workflow**: Human review and correction before final approval

## Security Considerations

- API keys should be stored securely (use environment variables in production)
- File uploads should be validated and sanitized
- Database should be backed up regularly
- Consider rate limiting for production use

## Performance Tips

- Use high-quality scans (300 DPI) for better OCR accuracy
- Process documents in batches for efficiency
- Monitor API quotas for Gemini usage
- Consider caching for frequently accessed data

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API logs for error messages
3. Ensure all dependencies are properly installed
4. Verify system requirements are met
