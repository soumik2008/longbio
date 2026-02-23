from flask import Flask, request, jsonify
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import os

# Initialize Flask app
app = Flask(__name__)

# Constants
key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
freefire_version = "OB52"
url_bio = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"

# Setup protobuf
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API information"""
    return jsonify({
        "status": "online",
        "message": "FreeFire Bio Updater API",
        "endpoints": {
            "/": "This help message",
            "/update_bio": "GET: Update bio (requires token and bio parameters)",
            "/health": "Health check endpoint"
        },
        "usage": "https://your-domain.vercel.app/update_bio?token=YOUR_TOKEN&bio=YOUR_BIO",
        "example": "/update_bio?token=eyJhbGciOiJIUzI1NiIsInN2ciI6IjMiLCJ0eXAiOiJKV1QifQ...&bio=Hello%20World"
    })

@app.route('/update_bio', methods=['GET'])
def update_bio():
    """Main endpoint to update FreeFire bio"""
    try:
        # Get parameters from URL
        token = request.args.get('token')
        bio = request.args.get('bio')
        
        # Log request for debugging
        print(f"Received request - Token: {token[:20] if token else 'None'}..., Bio: {bio[:50] if bio else 'None'}...")
        
        # Validate parameters
        if not token:
            return jsonify({
                "success": False,
                "error": "Token is required",
                "message": "Please provide a valid JWT token",
                "usage": "?token=YOUR_TOKEN&bio=YOUR_BIO"
            }), 400
            
        if not bio:
            return jsonify({
                "success": False,
                "error": "Bio is required",
                "message": "Please provide bio text",
                "usage": "?token=YOUR_TOKEN&bio=YOUR_BIO"
            }), 400
        
        # Check bio length
        if len(bio) > 500:
            return jsonify({
                "success": False,
                "error": "Bio too long",
                "message": f"Bio length is {len(bio)} characters. Maximum allowed is 500 characters."
            }), 400
        
        # Create and populate the data message
        data = Data()
        data.field_2 = 17
        data.field_5.CopyFrom(EmptyMessage())
        data.field_6.CopyFrom(EmptyMessage())
        data.field_8 = bio
        data.field_9 = 1
        data.field_11.CopyFrom(EmptyMessage())
        data.field_12.CopyFrom(EmptyMessage())
        
        # Serialize and encrypt
        data_bytes = data.SerializeToString()
        padded_data = pad(data_bytes, AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Headers for the request
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": freefire_version,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        
        print(f"Sending request to FreeFire server...")
        
        # Make the request to FreeFire server
        response = requests.post(url_bio, headers=headers, data=encrypted_data, timeout=30)
        
        print(f"FreeFire response status: {response.status_code}")
        
        # Prepare response
        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "bio_updated": bio,
            "bio_length": len(bio),
            "token_used": token[:20] + "..." if len(token) > 20 else token
        }
        
        # Add response data if available
        if response.text:
            try:
                result["server_response"] = response.json()
            except:
                result["server_response_text"] = response.text[:200]
        
        # Add error details for non-200 responses
        if response.status_code != 200:
            result["error_details"] = f"HTTP {response.status_code}: {response.text[:100]}"
            
            if response.status_code == 401:
                result["error_message"] = "Token expired or invalid. Please get a new token."
            elif response.status_code == 403:
                result["error_message"] = "Access forbidden. Token might be invalid."
            elif response.status_code == 429:
                result["error_message"] = "Rate limited. Please try again later."
        
        return jsonify(result), response.status_code
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Connection Error",
            "message": "Cannot connect to FreeFire servers. Please check your internet connection."
        }), 503
        
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Timeout Error",
            "message": "Request to FreeFire server timed out. Server might be busy."
        }), 504
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }), 200

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        "error": "NOT_FOUND",
        "code": "NOT_FOUND",
        "message": "The requested endpoint does not exist",
        "available_endpoints": ["/", "/update_bio", "/health"],
        "documentation": "Please check the API documentation"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An internal server error occurred",
        "code": "500"
    }), 500

# This is critical for Vercel - must be named 'app'
app = app

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
