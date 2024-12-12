import os
import hashlib
from flask import Flask, request, jsonify
from web3 import Web3
import json

# Initialize Flask app
app = Flask(__name__)

# Directory to store uploaded video files temporarily
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to Ganache
ganache_url = 'http://127.0.0.1:7545'
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check if connected
if not web3.is_connected():
    print("Failed to connect to Ganache")
    exit()

# Load contract ABI and address
with open('video_storage_abi.json') as f:  # Update this path if needed
    abi_data = json.load(f)
    contract_abi = abi_data['abi']
contract_address = '0x3b50cB9fd423943D915570D8b84C397a1b8D2150'  # Update with your deployed contract address

# Create contract instance
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Custom hashing logic

def custom_hash_video(file_path):
    """
    Custom multi-step hashing logic for a video file.
    Combines chunking, salting, XOR operations, and cryptographic hashing.
    """
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks
    SALT = b"unique_salt_value_2024"  # Static salt for simplicity (can be made dynamic)

    intermediate_hashes = []

    # Step 1: Process the video in chunks
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            # Step 2: Add salt to the chunk
            salted_chunk = bytearray()
            for i in range(len(chunk)):
                salted_byte = chunk[i] ^ SALT[i % len(SALT)]  # XOR each byte with the salt
                salted_chunk.append(salted_byte)

            # Step 3: Compute an intermediate hash (SHA-256)
            intermediate_hash = hashlib.sha256(salted_chunk).digest()
            intermediate_hashes.append(intermediate_hash)

    # Step 4: Combine intermediate hashes using XOR
    combined_hash = intermediate_hashes[0]
    for h in intermediate_hashes[1:]:
        combined_hash = bytes(a ^ b for a, b in zip(combined_hash, h))

    # Step 5: Finalize with SHA-512
    final_hash = hashlib.sha512(combined_hash).hexdigest()

    return final_hash

# Store hash in blockchain
def store_hash(hash_value, account):
    exists = contract.functions.checkVideoHash(hash_value).call()
    if exists:
        return {'error': f"Hash '{hash_value}' already exists."}

    # Store hash if it doesn't exist
    tx_hash = contract.functions.storeVideoHash(hash_value).transact({'from': account})
    return {'message': f"Hash '{hash_value}' stored successfully.", 'transaction_hash': tx_hash.hex()}

# Check if a hash exists in the blockchain
def check_hash(hash_value):
    exists = contract.functions.checkVideoHash(hash_value).call()
    return {'exists': exists}

# API route to handle video uploads
@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file in the request'}), 400
    
    video = request.files['video']
    
    if video.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the video temporarily
    video_path = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(video_path)
    
    # Hash the video
    video_hash = custom_hash_video(video_path)
    account = web3.eth.accounts[0]  # Replace with your Ethereum account

    # Store hash in blockchain
    result = store_hash(video_hash, account)
    
    # Clean up by removing the saved video file
    os.remove(video_path)
    print(result)
    return jsonify(result)

# API route to check if a hash exists
@app.route('/check_hash', methods=['POST'])
def check_video_hash():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video = request.files['video']

    if video.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded video file to the server
    video_path = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(video_path)

    # Calculate the hash of the uploaded video file
    video_hash = custom_hash_video(video_path)

    # Check if the hash exists in the blockchain
    result = check_hash(video_hash)

    # Clean up by removing the uploaded video file
    os.remove(video_path)
    print(result)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # You can change the host and port if needed
