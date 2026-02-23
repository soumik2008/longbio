from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import requests
import json
import base64
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fixed encryption key and IV (same as original)
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
FREEIRE_VERSION = "OB52"
URL_BIO = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Protobuf setup (same as original)
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)

# Check if Data class exists, if not create it dynamically
try:
    Data = _sym_db.GetSymbol('Data')
    EmptyMessage = _sym_db.GetSymbol('EmptyMessage')
except:
    # Fallback in case protobuf deserialization fails
    class EmptyMessage(object):
        pass
    
    class Data(object):
        def __init__(self):
            self.field_2 = 0
            self.field_5 = EmptyMessage()
            self.field_6 = EmptyMessage()
            self.field_8 = ""
            self.field_9 = 0
            self.field_11 = EmptyMessage()
            self.field_12 = EmptyMessage()
        
        def SerializeToString(self):
            # Simplified serialization for fallback
            return b''

def encrypt_bio(bio_text):
    """Encrypt bio data using AES-CBC"""
    try:
        data = Data()
        data.field_2 = 17
        data.field_5 = EmptyMessage()
        data.field_6 = EmptyMessage()
        data.field_8 = bio_text
        data.field_9 = 1
        data.field_11 = EmptyMessage()
        data.field_12 = EmptyMessage()
        
        data_bytes = data.SerializeToString()
        if not data_bytes:
            # If protobuf serialization fails, use a simple alternative
            data_bytes = f"{bio_text}".encode('utf-8')
        
        padded_data = pad(data_bytes, AES.block_size)
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Format as hex string without spaces
        return encrypted_data.hex().upper()
    except Exception as e:
        # Fallback encryption method
        data_bytes = f"{bio_text}".encode('utf-8')
        padded_data = pad(data_bytes, AES.block_size)
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        encrypted_data = cipher.encrypt(padded_data)
        return encrypted_data.hex().upper()

def update_freefire_bio(jwt_token, bio_text):
    """Send request to Free Fire API"""
    try:
        # Encrypt the bio
        encrypted_hex = encrypt_bio(bio_text)
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        
        # Headers for the request
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {jwt_token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FREEIRE_VERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        
        # Send request to Free Fire
        response = requests.post(URL_BIO, headers=headers, data=encrypted_bytes, timeout=30)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "message": "Bio updated successfully" if response.status_code == 200 else f"Failed with status {response.status_code}",
            "response": response.text[:500]  # Limit response size
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Exception occurred"
        }

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Free Fire Bio Update API",
        "endpoints": {
            "update_bio": "/update_bio?token={jwt_token}&bio={bio_text}",
            "docs": "/docs"
        },
        "example": "https://yourdomain.com/update_bio?token=YOUR_JWT_TOKEN&bio=Hello%20World",
        "deployed_on": os.environ.get('RENDER_SERVICE_NAME', 'local')
    })

@app.route('/docs')
def docs():
    return jsonify({
        "api_name": "Free Fire Bio Updater API",
        "version": "1.0",
        "description": "Update Free Fire profile bio using JWT token",
        "endpoint": "/update_bio",
        "method": "GET",
        "parameters": [
            {
                "name": "token",
                "type": "string",
                "required": True,
                "description": "Your Free Fire JWT token"
            },
            {
                "name": "bio",
                "type": "string",
                "required": True,
                "description": "The bio text to set (URL encoded)"
            }
        ],
        "example_request": "/update_bio?token=eyJhbGciOiJIUzI1NiIsInN2ciI6IjMiLCJ0eXAiOiJKV1QifQ...&bio=Hello%20World",
        "example_response": {
            "success": True,
            "status_code": 200,
            "message": "Bio updated successfully",
            "bio_length": 50,
            "token_preview": "eyJhbGciOiJIUzI1NiIs...",
            "freefire_response": "..."
        },
        "error_responses": [
            {"code": 400, "message": "Missing token or bio parameter"},
            {"code": 401, "message": "Invalid or expired token"},
            {"code": 500, "message": "Internal server error"}
        ]
    })

@app.route('/update_bio', methods=['GET'])
def update_bio():
    """Main endpoint to update Free Fire bio"""
    # Get parameters from request
    jwt_token = request.args.get('token')
    bio_text = request.args.get('bio')
    
    # Validate parameters
    if not jwt_token:
        return jsonify({
            "success": False,
            "error": "Missing token parameter",
            "usage": "/update_bio?token=YOUR_JWT_TOKEN&bio=YOUR_BIO_TEXT"
        }), 400
    
    if not bio_text:
        return jsonify({
            "success": False,
            "error": "Missing bio parameter",
            "usage": "/update_bio?token=YOUR_JWT_TOKEN&bio=YOUR_BIO_TEXT"
        }), 400
    
    # Check bio length
    if len(bio_text) > 500:
        return jsonify({
            "success": False,
            "error": "Bio too long. Maximum 500 characters allowed.",
            "current_length": len(bio_text)
        }), 400
    
    # Update bio
    result = update_freefire_bio(jwt_token, bio_text)
    
    # Add additional info to response
    response_data = {
        "success": result["success"],
        "status_code": result.get("status_code"),
        "message": result.get("message"),
        "bio_length": len(bio_text),
        "bio_preview": bio_text[:100] + "..." if len(bio_text) > 100 else bio_text,
        "token_preview": jwt_token[:30] + "..." if len(jwt_token) > 30 else jwt_token
    }
    
    # Add error or response details
    if "error" in result:
        response_data["error"] = result["error"]
    if "response" in result:
        response_data["freefire_response"] = result["response"]
    
    # Set appropriate HTTP status code
    http_status = 200 if result["success"] else (result.get("status_code", 500))
    
    return jsonify(response_data), http_status

@app.route('/update_bio_post', methods=['POST'])
def update_bio_post():
    """POST endpoint for updating bio (supports JSON)"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Invalid JSON data"
        }), 400
    
    jwt_token = data.get('token')
    bio_text = data.get('bio')
    
    # Validate parameters
    if not jwt_token or not bio_text:
        return jsonify({
            "success": False,
            "error": "Missing token or bio in JSON",
            "required_fields": ["token", "bio"]
        }), 400
    
    # Update bio
    result = update_freefire_bio(jwt_token, bio_text)
    
    response_data = {
        "success": result["success"],
        "status_code": result.get("status_code"),
        "message": result.get("message"),
        "bio_length": len(bio_text)
    }
    
    if "error" in result:
        response_data["error"] = result["error"]
    
    http_status = 200 if result["success"] else (result.get("status_code", 500))
    
    return jsonify(response_data), http_status

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/docs", "/update_bio", "/update_bio_post"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

# For Vercel serverless deployment
def handler(event, context):
    return app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("Free Fire Bio Update API")
    print("=" * 50)
    print(f"Server starting on port {port}...")
    print("Local URL: http://127.0.0.1:5000")
    print("Example usage:")
    print("  GET  /update_bio?token=YOUR_TOKEN&bio=Hello%20World")
    print("  POST /update_bio_post (JSON: {\"token\": \"...\", \"bio\": \"...\"})")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
