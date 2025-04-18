import json
import os
import bcrypt
from datetime import datetime
from pathlib import Path

# Ensure data directory exists
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"

def load_users():
    """Load users from JSON file."""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(username, password):
    """Register a new user."""
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        'password': hash_password(password),
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'vcs': []
    }
    
    save_users(users)
    return True, "User registered successfully"

def login_user(username, password):
    """Login a user."""
    users = load_users()
    
    if username not in users:
        return False, "User not found"
    
    if not verify_password(password, users[username]['password']):
        return False, "Invalid password"
    
    return True, "Login successful"

def get_user_vcs(username):
    """Get VCs for a user."""
    users = load_users()
    if username in users:
        return users[username]['vcs']
    return []

def save_user_vcs(username, vcs):
    """Save VCs for a user."""
    users = load_users()
    if username in users:
        users[username]['vcs'] = vcs
        save_users(users)
        return True
    return False 