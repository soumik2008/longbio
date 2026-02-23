from flask import Flask, request, jsonify
import requests
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import os

app = Flask(__name__)

# Constants
freefire_version = "OB52"
url_bio = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"
key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# Hardcoded proto structure (to avoid protobuf issues on Vercel)
def create_proto_message(bio_text):
    """
    Manually create the protobuf message structure
    Field numbers and structure based on the original proto
    """
    # Message structure:
    # field_2 = 17 (int)
    # field_5 = EmptyMessage
    # field_6 = EmptyMessage
    # field_8 = bio (string)
    # field_9 = 1 (int)
    # field_11 = EmptyMessage
    # field_12 = EmptyMessage
    
    # EmptyMessage is just empty bytes
    empty_message = b''
    
    # Build the message manually using protobuf wire format
    # Field 2 (varint) = 17
    msg = b'\x10\x11'  # field 2, value 17
    
    # Field 5 (length-delimited) - EmptyMessage
    msg += b'\x2a\x00'  # field 5, length 0
    
    # Field 6 (length-delimited) - EmptyMessage
    msg += b'\x32\x00'  # field 6, length 0
    
    # Field 8 (string) - bio
    bio_bytes = bio_text.encode('utf-8')
    bio_len = len(bio_bytes)
    if bio_len <= 0x7f:
        msg += b'\x42' + bytes([bio_len]) + bio_bytes
    else:
        # Handle longer strings (though bio usually short)
        msg += b'\x42' + encode_varint(bio_len) + bio_bytes
    
    # Field 9 (varint) = 1
    msg += b'\x48\x01'  # field 9, value 1
    
    # Field 11 (length-delimited) - EmptyMessage
    msg += b'\x5a\x00'  # field 11, length 0
    
    # Field 12 (length-delimited) - EmptyMessage
    msg += b'\x62\x00'  # field 12, length 0
    
    return msg

def encode_varint(value):
    """Encode an integer as varint"""
    result = []
    while True:
        byte = value & 0x7f
        value >>= 7
        if value:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            break
    return bytes(result)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>FreeFire Bio Updater</title>
            <style>
                body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                code { background: #f4f4f4; padding: 5px; border-radius: 3px; }
                .endpoint { background: #e8f4f8; padding: 10px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>🔥 FreeFire Bio Updater API</h1>
            <p>Status: <strong style="color: green">✅ ONLINE</strong></p>
            
            <div class="endpoint">
                <h3>📝 Update Bio Endpoint:</h3>
                <code>GET /update_bio?token=YOUR_TOKEN&bio=YOUR_BIO</code>
            </div>
            
            <div class="endpoint">
                <h3>📊 Test Endpoint:</h3>
                <code>GET /test</code>
            </div>
            
            <h3>Example:</h3>
            <code>/update_bio?token=eyJhbGc...&bio=Hello%20World</code>
            
            <h3>Response Format:</h3>
            <pre>{
  "success": true/false,
  "status_code": 200,
  "message": "Bio updated!",
  "bio": "your bio here"
}</pre>
        </body>
    </html>
    """

@app.route('/test')
def test():
    return jsonify({
        "status": "✅ WORKING",
        "message": "API is running successfully on Vercel!",
        "version": freefire_version,
        "endpoints": {
            "home": "/",
            "test": "/test",
            "update_bio": "/update_bio?token=TOKEN&bio=BIO"
        }
    })

@app.route('/update_bio', methods=['GET'])
def update_bio():
    try:
        # Get parameters
        token = request.args.get('token')
        bio = request.args.get('bio')
        
        # Validate
        if not token or not bio:
            return jsonify({
                "success": False,
                "error": "Missing token or bio! Use: ?token=XXX&bio=XXX"
            }), 400
        
        if len(bio) > 500:
            return jsonify({
                "success": False,
                "error": f"Bio too long! Max 500 chars, yours: {len(bio)}"
            }), 400
        
        print(f"[*] Updating bio: {bio[:50]}...")
        
        # Create proto message manually
        proto_message = create_proto_message(bio)
        
        # Encrypt
        padded_data = pad(proto_message, AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Headers
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
        
        # Send request
        res = requests.post(
            url_bio, 
            headers=headers, 
            data=encrypted_data,
            timeout=30
        )
        
        # Return response
        response = {
            "success": res.status_code == 200,
            "status_code": res.status_code,
            "bio": bio,
            "bio_length": len(bio)
        }
        
        if res.status_code == 200:
            response["message"] = "✅ Bio updated successfully!"
            try:
                response["server_response"] = res.json()
            except:
                response["server_response"] = res.text[:200]
        else:
            response["error"] = f"❌ Failed with status {res.status_code}"
            response["details"] = res.text[:200]
            
            if res.status_code == 401:
                response["fix"] = "Token expired! Get new token"
            elif res.status_code == 403:
                response["fix"] = "Invalid token or banned"
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": str(type(e).__name__)
        }), 500

# Vercel handler
def handler(request, context):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
