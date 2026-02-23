from flask import Flask, request, jsonify
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import base64
import os

app = Flask(__name__)

# Constants
key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
freefire_version = "OB52"
url_bio = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"

# Protobuf setup
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

def encrypt_bio(bio_text):
    """Encrypt bio data using AES-CBC"""
    data = Data()
    data.field_2 = 17
    data.field_5.CopyFrom(EmptyMessage())
    data.field_6.CopyFrom(EmptyMessage())
    data.field_8 = bio_text
    data.field_9 = 1
    data.field_11.CopyFrom(EmptyMessage())
    data.field_12.CopyFrom(EmptyMessage())
    
    data_bytes = data.SerializeToString()
    padded_data = pad(data_bytes, AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(padded_data)
    
    return encrypted_data

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Free Fire Bio Updater API",
        "usage": "/update_bio?token=YOUR_TOKEN&bio=YOUR_BIO",
        "example": "/update_bio?token=eyJ...&bio=Hello%20World",
        "note": "Use URL encoding for special characters in bio"
    })

@app.route('/update_bio', methods=['GET', 'POST'])
def update_bio():
    try:
        # Get parameters from URL (GET) or JSON body (POST)
        if request.method == 'GET':
            token = request.args.get('token')
            bio = request.args.get('bio')
        else:  # POST
            data = request.get_json(silent=True) or {}
            token = data.get('token') or request.args.get('token')
            bio = data.get('bio') or request.args.get('bio')
        
        # Validate inputs
        if not token:
            return jsonify({"error": "Token is required", "status": "failed"}), 400
        
        if not bio:
            return jsonify({"error": "Bio is required", "status": "failed"}), 400
        
        # Bio length check
        if len(bio) > 500:
            return jsonify({"error": "Bio too long! Maximum 500 characters", "status": "failed"}), 400
        
        # Encrypt bio
        encrypted_data = encrypt_bio(bio)
        
        # Prepare headers
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
        
        # Send request to Free Fire server
        response = requests.post(
            url_bio, 
            headers=headers, 
            data=encrypted_data, 
            timeout=30
        )
        
        # Prepare result
        result = {
            "status_code": response.status_code,
            "bio": bio,
            "bio_length": len(bio)
        }
        
        if response.status_code == 200:
            result["status"] = "success"
            result["message"] = "Bio updated successfully!"
            
            # Try to parse response
            if response.text:
                try:
                    result["response"] = response.json()
                except:
                    result["response_text"] = response.text[:200]
        else:
            result["status"] = "failed"
            result["error"] = f"HTTP {response.status_code}"
            result["response"] = response.text[:200] if response.text else "No response"
            
            if response.status_code == 401:
                result["error_details"] = "Token expired or invalid"
            elif response.status_code == 403:
                result["error_details"] = "Access forbidden"
        
        return jsonify(result)
        
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connection error", "status": "failed"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout", "status": "failed"}), 504
    except Exception as e:
        return jsonify({"error": str(e), "status": "failed"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)