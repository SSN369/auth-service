# app/models/user_management.py
from app import  bcrypt
from app.extension import db
from datetime import datetime
from app.models.department import Department
# Assuming Department model might be in master_data.py or a similar file
# If not, and you want to define it here, you can. Otherwise, ensure it's imported.
# from .master_data import Department # Example if Department is in master_data.py

# role_permissions association table
# Your SQL schema has a created_at for this table.
# If SQLAlchemy should manage it, you can add it. Otherwise, DB default is fine.
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.permission_id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow) # Matches your SQL schema
)

class Role(db.Model):
    __tablename__ = 'roles'

    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    permissions = db.relationship(
        'Permission', 
        secondary=role_permissions,
        lazy='selectin', # Efficiently loads permissions for a role
        backref=db.backref('roles', lazy=True) # Allows perm.roles
    )
    
    users = db.relationship('User', back_populates='role') # Link back to users

    def __repr__(self):
        return f'<Role {self.role_name}>'

class Permission(db.Model):
    __tablename__ = 'permissions'

    permission_id = db.Column(db.Integer, primary_key=True)
    permission_name = db.Column(db.String(100), unique=True, nullable=False)
    module = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Permission {self.permission_name}>'

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True) # Schema allows NULL for email, but unique if present
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'), nullable=True) # Ensure Department model is defined
    
    is_active = db.Column(db.Boolean, default=True, nullable=False) # Crucial for the previous error
    last_login = db.Column(db.DateTime, nullable=True)
    
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', name='fk_user_created_by'), nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', name='fk_user_updated_by'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    role = db.relationship('Role', back_populates='users', lazy='joined') # Eager load role for quick access

    # Assuming Department model is defined elsewhere (e.g., app.models.master_data.Department)
    # If Department model is defined in *this* file, you can use Department directly.
    # If it's defined *after* User in this file, or in another file that might cause import cycle,
    # use string 'Department'.
    department = db.relationship('Department', foreign_keys=[department_id], lazy='select') 
                                   
    creator = db.relationship('User', foreign_keys=[created_by_user_id], remote_side=[user_id], backref='created_users')
    updater = db.relationship('User', foreign_keys=[updated_by_user_id], remote_side=[user_id], backref='updated_users')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_permissions_list(self):
        if self.role and self.role.permissions:
            return [perm.permission_name for perm in self.role.permissions]
        return []

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_name': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role.role_name if self.role else None,
            'role_id': self.role_id,
            'department_id': self.department_id,
            # 'departmentName': self.department.department_name if self.department else None, # If you load department
            'is_active': self.is_active,
            'lastLogin': self.last_login.isoformat() if self.last_login else None,
            'permissions': self.get_permissions_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<User {self.username}>'

# You also need a Department model for the User.department_id ForeignKey.
# This should ideally be in a file like app/models/master_data.py or a dedicated one for organization.
# For completeness, if it's not defined elsewhere, here's a minimal stub.
# If it IS defined elsewhere (e.g., app.models.master_data), ensure it's imported or referenced correctly.
