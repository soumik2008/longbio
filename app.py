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

app = Flask(__name__)

# Constants
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
FREEIRE_VERSION = "OB52"
URL_BIO = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"

# Protocol buffer setup
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

def encrypt_bio_data(bio_text):
    """Encrypt bio data using AES-CBC"""
    try:
        # Create and populate the data message
        data = Data()
        data.field_2 = 17
        data.field_5.CopyFrom(EmptyMessage())
        data.field_6.CopyFrom(EmptyMessage())
        data.field_8 = bio_text
        data.field_9 = 1
        data.field_11.CopyFrom(EmptyMessage())
        data.field_12.CopyFrom(EmptyMessage())

        # Serialize and encrypt
        data_bytes = data.SerializeToString()
        padded_data = pad(data_bytes, AES.block_size)
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        encrypted_data = cipher.encrypt(padded_data)
        
        return encrypted_data
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Free Fire Bio Update API",
        "endpoint": "/update_bio?token={token}&bio={bio}",
        "version": FREEIRE_VERSION
    })

@app.route('/update_bio', methods=['GET'])
def update_bio():
    try:
        # Get parameters from URL
        token = request.args.get('token')
        bio = request.args.get('bio')
        
        # Validate parameters
        if not token:
            return jsonify({
                "success": False,
                "error": "Token is required",
                "message": "Please provide token parameter"
            }), 400
            
        if not bio:
            return jsonify({
                "success": False,
                "error": "Bio is required",
                "message": "Please provide bio parameter"
            }), 400
            
        # Check bio length
        if len(bio) > 500:
            return jsonify({
                "success": False,
                "error": "Bio too long",
                "message": "Bio should be less than 500 characters"
            }), 400
        
        # Encrypt bio data
        try:
            encrypted_data = encrypt_bio_data(bio)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "Encryption failed",
                "message": str(e)
            }), 500
        
        # Prepare headers
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FREEIRE_VERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        
        # Send request to Free Fire server
        try:
            response = requests.post(
                URL_BIO, 
                headers=headers, 
                data=encrypted_data, 
                timeout=30
            )
            
            # Parse response
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "bio": bio
            }
            
            # Add response data if available
            if response.text:
                try:
                    result["response"] = response.json()
                except:
                    result["response_text"] = response.text[:200]
            
            # Add error message for failed requests
            if response.status_code != 200:
                result["error"] = "Failed to update bio"
                if response.status_code == 401:
                    result["message"] = "Token expired or invalid"
                elif response.status_code == 403:
                    result["message"] = "Access forbidden"
                else:
                    result["message"] = f"Server returned status {response.status_code}"
            
            return jsonify(result), response.status_code
            
        except requests.exceptions.ConnectionError:
            return jsonify({
                "success": False,
                "error": "Connection Error",
                "message": "Failed to connect to Free Fire server"
            }), 503
            
        except requests.exceptions.Timeout:
            return jsonify({
                "success": False,
                "error": "Timeout",
                "message": "Request timed out"
            }), 504
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "Request Failed",
                "message": str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "NOT_FOUND",
        "message": "Endpoint not found. Use /update_bio?token={token}&bio={bio}"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An internal server error occurred"
    }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
