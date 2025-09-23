# FRA OCR Integration Guide

This guide explains how to integrate the OCR functionality with your FRA Atlas WebGIS system.

## Overview

The OCR integration provides:
- **Document Upload**: Drag-and-drop interface for PDF/image uploads
- **Automated Processing**: Tesseract OCR + Gemini AI extraction
- **Data Validation**: Human review and correction interface
- **Database Integration**: Automatic saving to SQLite database
- **WebGIS Integration**: Seamless integration with existing claims management

## Quick Start

### 1. Install Dependencies

```bash
cd OCR
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH

**macOS:**
```bash
brew install tesseract
```

**Ubuntu:**
```bash
sudo apt-get install tesseract-ocr
```

### 3. Configure Gemini API

1. Get API key from Google AI Studio
2. Update `flask_ocr_api.py` line 22:
   ```python
   genai.configure(api_key="YOUR_API_KEY_HERE")
   ```

### 4. Start the OCR API

```bash
# Windows
start_ocr.bat

# Linux/Mac
./start_ocr.sh

# Or directly
python start_ocr_api.py
```

### 5. Test the Integration

```bash
python test_ocr.py
```

## Integration Points

### Frontend Integration

The OCR functionality is integrated into the FRA Claims Management page:

1. **Upload Button**: Added "Upload Document" button next to "Add New Claim"
2. **Modal Interface**: Full-screen modal for document upload and processing
3. **Progress Indicators**: Real-time processing status updates
4. **Data Preview**: Extracted data review and correction interface

### Backend Integration

1. **Flask API**: RESTful API for OCR processing
2. **Database Schema**: Extended SQLite schema for OCR data
3. **Error Handling**: Comprehensive error handling and user feedback
4. **File Validation**: File type and size validation

## API Endpoints

### Document Processing
```http
POST /api/upload-document
Content-Type: multipart/form-data

Body: file (PDF/JPG/PNG)
Response: {
  "filename": "document.pdf",
  "raw_text": "extracted text...",
  "confidence": 85.5,
  "extracted_data": {
    "claimant_name": "John Doe",
    "village": "Test Village",
    "district": "Test District"
  },
  "full_address": "Test Village, Test District"
}
```

### Save Claim
```http
POST /api/save-claim
Content-Type: application/json

Body: {
  "filename": "document.pdf",
  "claimant_name": "John Doe",
  "village": "Test Village",
  "district": "Test District",
  "land_area": "2.5",
  "is_scheduled_tribe": "Yes",
  "full_address": "Test Village, Test District",
  "raw_text": "extracted text...",
  "confidence": 85.5
}
```

### Get Claims
```http
GET /api/claims
Response: {
  "claims": [
    {
      "id": 1,
      "source_filename": "document.pdf",
      "claimant_name": "John Doe",
      "village": "Test Village",
      "district": "Test District",
      "status": "pending_review",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

## Data Flow

```
1. User uploads document
   ↓
2. Frontend validates file type/size
   ↓
3. Document sent to Flask API
   ↓
4. Tesseract OCR extracts text
   ↓
5. Gemini AI structures the data
   ↓
6. Confidence score calculated
   ↓
7. Data returned to frontend
   ↓
8. User reviews/corrects data
   ↓
9. Data saved to database
   ↓
10. Claims table updated
```

## Configuration

### Tesseract Configuration

The system auto-detects Tesseract installation. For custom paths:

```python
# Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Linux/Mac (usually works with default PATH)
```

### Database Configuration

The system uses SQLite with this schema:

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

## Error Handling

### Common Errors

1. **Tesseract not found**
   - Solution: Install Tesseract OCR
   - Check PATH configuration

2. **Gemini API errors**
   - Solution: Verify API key
   - Check internet connection
   - Verify API quota

3. **File upload errors**
   - Solution: Check file type/size
   - Verify file permissions

4. **Database errors**
   - Solution: Check SQLite installation
   - Verify file permissions

### Error Responses

```json
{
  "error": "Error message",
  "details": "Additional error details"
}
```

## Performance Optimization

### OCR Accuracy
- Use high-quality scans (300 DPI minimum)
- Ensure good contrast and lighting
- Avoid skewed or rotated documents

### Processing Speed
- Process documents in batches
- Use appropriate image resolution
- Monitor API rate limits

### Database Performance
- Regular database backups
- Index frequently queried fields
- Monitor database size

## Security Considerations

### API Security
- Use HTTPS in production
- Implement rate limiting
- Validate all inputs

### Data Privacy
- Secure API key storage
- Encrypt sensitive data
- Regular security audits

### File Handling
- Validate file types
- Scan for malware
- Limit file sizes

## Troubleshooting

### Debug Mode

Enable debug mode for detailed logging:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Log Files

Check console output for error messages and processing logs.

### Test Script

Run the test script to verify all components:

```bash
python test_ocr.py
```

## Production Deployment

### Environment Variables

```bash
export GEMINI_API_KEY="your_api_key_here"
export TESSERACT_CMD="/usr/bin/tesseract"
export DATABASE_URL="sqlite:///fra_claims.db"
```

### Process Management

Use a process manager like PM2 or systemd:

```bash
# PM2
pm2 start flask_ocr_api.py --name fra-ocr-api

# systemd
sudo systemctl start fra-ocr-api
```

### Reverse Proxy

Configure Nginx or Apache as reverse proxy:

```nginx
location /api/ {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Monitoring

### Health Checks

```bash
curl http://localhost:5000/api/health
```

### Metrics

Monitor:
- API response times
- OCR processing accuracy
- Database performance
- Error rates

## Support

For issues or questions:
1. Check this integration guide
2. Review error logs
3. Run the test script
4. Verify all dependencies

## Future Enhancements

### Planned Features
- Batch processing
- Advanced image preprocessing
- Multi-language support
- Cloud storage integration
- Real-time collaboration

### API Versioning
- Current: v1
- Future: v2 with enhanced features

## License

This OCR integration is part of the FRA Atlas WebGIS system and follows the same licensing terms.
