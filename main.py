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
import os
import sys
from flask_cors import CORS

# Vercel serverless handler ke liye
from http.server import BaseHTTPRequestHandler
from flask import Response

app = Flask(__name__)
CORS(app)

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fixed encryption key and IV
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
FREEIRE_VERSION = "OB52"
URL_BIO = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Protobuf setup - Simplified for Vercel
_sym_db = _symbol_database.Default()

try:
    DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
    _globals = globals()
    _builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
    _builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)
    Data = _sym_db.GetSymbol('Data')
    EmptyMessage = _sym_db.GetSymbol('EmptyMessage')
except Exception as e:
    print(f"Protobuf setup warning: {e}")
    # Fallback classes
    class EmptyMessage:
        def __init__(self):
            pass
        def CopyFrom(self, other):
            pass
    
    class Data:
        def __init__(self):
            self.field_2 = 0
            self.field_5 = None
            self.field_6 = None
            self.field_8 = ""
            self.field_9 = 0
            self.field_11 = None
            self.field_12 = None
        
        def SerializeToString(self):
            # Simple serialization
            return f"{self.field_2}:{self.field_8}:{self.field_9}".encode()
    
    EmptyMessage = EmptyMessage
    Data = Data

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
        padded_data = pad(data_bytes, AES.block_size)
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        encrypted_data = cipher.encrypt(padded_data)
        
        return encrypted_data.hex().upper()
    except Exception as e:
        print(f"Encryption error: {e}")
        raise

def update_freefire_bio(jwt_token, bio_text):
    """Send request to Free Fire API"""
    try:
        encrypted_hex = encrypt_bio(bio_text)
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        
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
        
        response = requests.post(URL_BIO, headers=headers, data=encrypted_bytes, timeout=30)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "message": "Bio updated successfully" if response.status_code == 200 else f"Failed with status {response.status_code}",
            "response": response.text[:500]
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
            "docs": "/docs",
            "health": "/health"
        },
        "example": "https://your-domain.vercel.app/update_bio?token=YOUR_JWT_TOKEN&bio=Hello%20World"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "environment": "vercel",
        "python_version": sys.version
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
            {"name": "token", "type": "string", "required": True, "description": "Your Free Fire JWT token"},
            {"name": "bio", "type": "string", "required": True, "description": "The bio text to set (URL encoded)"}
        ],
        "example_request": "/update_bio?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&bio=Hello%20World"
    })

@app.route('/update_bio', methods=['GET'])
def update_bio():
    jwt_token = request.args.get('token')
    bio_text = request.args.get('bio')
    
    if not jwt_token or not bio_text:
        return jsonify({
            "success": False,
            "error": "Missing token or bio parameter",
            "usage": "/update_bio?token=YOUR_JWT_TOKEN&bio=YOUR_BIO_TEXT"
        }), 400
    
    if len(bio_text) > 500:
        return jsonify({
            "success": False,
            "error": "Bio too long. Maximum 500 characters allowed."
        }), 400
    
    result = update_freefire_bio(jwt_token, bio_text)
    
    response_data = {
        "success": result["success"],
        "status_code": result.get("status_code"),
        "message": result.get("message"),
        "bio_length": len(bio_text)
    }
    
    if "error" in result:
        response_data["error"] = result["error"]
    if "response" in result:
        response_data["freefire_response"] = result["response"]
    
    return jsonify(response_data), 200 if result["success"] else (result.get("status_code", 500))

@app.route('/update_bio_post', methods=['POST'])
def update_bio_post():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON data"}), 400
    
    jwt_token = data.get('token')
    bio_text = data.get('bio')
    
    if not jwt_token or not bio_text:
        return jsonify({
            "success": False,
            "error": "Missing token or bio in JSON"
        }), 400
    
    result = update_freefire_bio(jwt_token, bio_text)
    
    return jsonify({
        "success": result["success"],
        "status_code": result.get("status_code"),
        "message": result.get("message"),
        "bio_length": len(bio_text)
    }), 200 if result["success"] else (result.get("status_code", 500))

# Vercel serverless handler - YEH IMPORTANT HAI
def handler(request, context):
    """Vercel serverless function handler"""
    return app

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5009))
    app.run(host='0.0.0.0', port=port, debug=True)