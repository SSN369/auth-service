# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash # If you were using this directly
from app.models.user_management import User, Role # Add other models if needed # Role and Permission might not be directly needed here, but User model uses them
from app import bcrypt # Import db and bcrypt from app/__init__.py
from app.extension import db
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required, 
    get_jwt_identity,
    get_jwt # For potential blacklisting if you implement it later
)
from datetime import timedelta # If you want to set custom expiration times here

# Create a Blueprint for auth routes
# This blueprint is registered in app/__init__.py with url_prefix='/api/auth'
auth_bp = Blueprint('auth_bp', __name__)
# ... (other imports)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print("the username and passs format is :", data)
    if not data:
        return jsonify({"success": False, "message": "No input data provided"}), 400

    username = data.get('username')
    password = data.get('password')
    print(username, password)

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({"success": False, "message": "User account is inactive."}), 403

        # --- THIS IS THE REQUIRED CHANGE ---
        # 1. Create a dictionary of extra data (claims) to put inside the token.
        # We are adding the user's role name here.
        additional_claims = {"role": user.role.role_name}
        #print(type(user.user_id))
        # 2. Pass these claims when creating the access token.
        # Ensure identity is a string to avoid "Subject must be a string" errors
        access_token = create_access_token(
            identity=str(user.user_id), 
            additional_claims=additional_claims
        )

        print("the access token is :", access_token)
        # --- END OF CHANGE ---
        print(type(access_token), access_token)
        refresh_token = create_refresh_token(identity=str(user.user_id))

        try:
            user.last_login = db.func.now()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating last_login for user {user.username}: {e}")

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict() 
        }), 200
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()  # already int

    user = User.query.get(current_user_id)
    if not user:
        return jsonify(success=False, message="User not found."), 404
    if not user.is_active:
        return jsonify(success=False, message="User account is inactive."), 403

    return jsonify(success=True, data=user.to_dict()), 200



@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()  # int

    user = User.query.get(current_user_id)
    if not user:
        return jsonify(success=False, message="User not found."), 401
    if not user.is_active:
        return jsonify(success=False, message="User account is inactive."), 403

    # Ensure refresh generates an access token with string identity
    new_access_token = create_access_token(identity=str(current_user_id))
    return jsonify(success=True, token=new_access_token), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required() # Requires a valid access token to "logout"
def logout():
    # For JWTs, logout is primarily a client-side action (deleting the token).
    # If you implement token blacklisting (e.g., storing JTI - JWT ID - of revoked tokens),
    # you would add the JTI to the blacklist here.
    # current_jti = get_jwt()['jti']
    # add_to_blacklist(current_jti) # Your custom blacklisting function
    
    return jsonify(success=True, message="Logout acknowledged. Client should clear tokens."), 200

# Example of how you might structure a registration route (you'll need to implement it fully)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No input data provided"}), 400

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    full_name = data.get('full_name')
    role_name = data.get('role_name', 'Operator') # Default role or get from input

    if not username or not password or not email:
        return jsonify({"success": False, "message": "Username, password, and email are required"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"success": False, "message": "Username or email already exists"}), 409 # Conflict

    target_role = Role.query.filter_by(role_name=role_name).first()
    if not target_role:
        return jsonify({"success": False, "message": f"Role '{role_name}' not found."}), 400
        
    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        role_id=target_role.role_id # Assign the role_id
        # department_id can be set if provided
    )
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        # You might want to log the user in directly by creating tokens, or just return success
        return jsonify({
            "success": True, 
            "message": "User registered successfully. Please log in.",
            "userId": new_user.user_id # Return the new user's ID
        }), 201 # Created
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {e}") # Log this error
        return jsonify({"success": False, "message": "Registration failed due to an internal error."}), 500
