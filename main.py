import hashlib
import datetime
import json
import pickle
import os
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash

# User class to manage user authentication
class User:
    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Block class for blockchain
class Block:
    def __init__(self, data, previous_hash, fee):
        self.data = data
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.previous_hash = previous_hash
        self.nonce = 0
        self.fee = fee
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "data": self.data,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "fee": self.fee
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

# Blockchain class to manage the chain
class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 4
        self.load_chain()
        self.users = {}

    def create_genesis_block(self):
        return Block("Genesis Block", "0", 0)

    def load_chain(self):
        if os.path.exists("blockchain.pkl"):
            with open("blockchain.pkl", "rb") as f:
                self.chain = pickle.load(f)
        else:
            self.chain.append(self.create_genesis_block())

    def add_block(self, data, fee):
        previous_hash = self.chain[-1].hash
        new_block = Block(data, previous_hash, fee)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.save_chain()

    def save_chain(self):
        with open("blockchain.pkl", "wb") as f:
            pickle.dump(self.chain, f)

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def register_user(self, username, password):
        if username in self.users:
            return False
        self.users[username] = User(username, password)
        return True

    def authenticate_user(self, username, password):
        user = self.users.get(username)
        return user and user.check_password(password)

# Flask web application
app = Flask(__name__)
blockchain = Blockchain()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    success = blockchain.register_user(username, password)
    return jsonify({"success": success})

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if blockchain.authenticate_user(username, password):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})

@app.route('/add_block', methods=['POST'])
def add_block():
    username = request.form['username']
    password = request.form['password']
    data = request.form['data']
    fee = float(request.form['fee'])
    if blockchain.authenticate_user(username, password):
        blockchain.add_block(data, fee)
        return jsonify({"success": True, "message": "Block added successfully!"})
    else:
        return jsonify({"success": False, "message": "Authentication failed!"})

@app.route('/verify_chain', methods=['GET'])
def verify_chain():
    is_valid = blockchain.verify_chain()
    return jsonify({"valid": is_valid})

if __name__ == "__main__":
    app.run(debug=True)