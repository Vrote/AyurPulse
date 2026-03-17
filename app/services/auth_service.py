from app.db.mongodb import db
from bson import ObjectId

users_collection = db["users"]
token_collection = db["tokens"]


def get_user_by_email(email: str):
    return users_collection.find_one({"email": email})


def create_user(user_data: dict):
    return users_collection.insert_one(user_data)


def store_refresh_token(user_id, token):
    token_collection.insert_one({
        "user_id": user_id,
        "token": token
    })


def delete_token(token):
    token_collection.delete_one({"token": token})