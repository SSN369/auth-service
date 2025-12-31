# In app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask import jsonify

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
ma = Marshmallow()


# JWT error handlers: return clear JSON + 401 instead of default 422 messages
@jwt.unauthorized_loader
def _unauthorized_loader(callback_msg):
	return jsonify({"msg": callback_msg}), 401


@jwt.invalid_token_loader
def _invalid_token_loader(callback_msg):
	return jsonify({"msg": callback_msg}), 401


@jwt.expired_token_loader
def _expired_token_loader(jwt_header, jwt_payload):
	return jsonify({"msg": "Token has expired"}), 401


@jwt.revoked_token_loader
def _revoked_token_loader(jwt_header, jwt_payload):
	return jsonify({"msg": "Token has been revoked"}), 401


@jwt.needs_fresh_token_loader
def _needs_fresh_token_loader(jwt_header, jwt_payload):
	return jsonify({"msg": "Fresh token required"}), 401
