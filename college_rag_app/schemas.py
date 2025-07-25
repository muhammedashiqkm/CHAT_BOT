from marshmallow import Schema, fields

class LoginSchema(Schema):
    """Schema for login request validation."""
    username = fields.String(required=True)
    password = fields.String(required=True)

class SessionSchema(Schema):
    """Schema for session management requests."""
    username = fields.String(required=True)
    session_name = fields.String(required=True)

class QuestionSchema(Schema):
    """Schema for the /ask endpoint request."""
    username = fields.String(required=True)
    session_name = fields.String(required=True)
    question = fields.String(required=True)