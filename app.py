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

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _globals['_DATA']._serialized_start = 15
    _globals['_DATA']._serialized_end = 202
    _globals['_EMPTYMESSAGE']._serialized_start = 204
    _globals['_EMPTYMESSAGE']._serialized_end = 218

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

# Constants
freefire_version = "OB52"
url_bio = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"
key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "FreeFire Bio Updater API",
        "usage": "/update_bio?token=YOUR_TOKEN&bio=YOUR_BIO"
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
                "error": "Token is required! Use ?token=YOUR_TOKEN"
            }), 400
            
        if not bio:
            return jsonify({
                "success": False,
                "error": "Bio is required! Use &bio=YOUR_BIO"
            }), 400
            
        # Check bio length
        if len(bio) > 500:
            return jsonify({
                "success": False,
                "error": f"Bio too long! Maximum 500 characters, yours: {len(bio)}"
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
        
        # Format encrypted data
        formatted_encrypted_data = ' '.join([f"{byte:02X}" for byte in encrypted_data])
        data_hex = formatted_encrypted_data
        data_bytes = bytes.fromhex(data_hex.replace(" ", ""))
        
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
        
        # Make the request
        res_bio = requests.post(url_bio, headers=headers, data=data_bytes, timeout=30)
        
        # Prepare response
        response_data = {
            "success": res_bio.status_code == 200,
            "status_code": res_bio.status_code,
            "bio": bio,
            "bio_length": len(bio)
        }
        
        # Add response details
        if res_bio.status_code == 200:
            response_data["message"] = "Bio updated successfully!"
            if res_bio.text:
                try:
                    response_data["response"] = res_bio.json()
                except:
                    response_data["response_text"] = res_bio.text[:200]
        else:
            response_data["error"] = f"Failed with status code: {res_bio.status_code}"
            response_data["response_text"] = res_bio.text[:200]
            
            if res_bio.status_code == 401:
                response_data["error_details"] = "Token expired! Get a new token."
            elif res_bio.status_code == 403:
                response_data["error_details"] = "Access forbidden. Token might be invalid."
        
        return jsonify(response_data)
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Connection error! Check your internet connection."
        }), 500
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Request timeout! Server might be down."
        }), 504
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "status": "working",
        "message": "API is running successfully!"
    })

# For local testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
