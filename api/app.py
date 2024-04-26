import spacy
import bcrypt
from pymongo import MongoClient
from flask_restful import Api, Resource
from flask import Flask, jsonify, request

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

def user_exist(username):
    count = users.count_documents({"Username": username})
    return count > 0

def verify_password(username, password):
    if not user_exist(username):
        return False

    hashed_password = users.find({"Username":username})[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_password) == hashed_password:
        return True
    else:
        return False

class Register(Resource):
    
    def post(self):
        post_data = request.get_json()

        username = post_data["username"]
        password = post_data["password"]

        if user_exist(username):
            
            return jsonify({
                "status": 301,
                "message": "Invalid Username"
            })
        
        hashed_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert_one({
            "Username": username,
            "Password": hashed_password
        })

        return jsonify({
            "status": 200,
            "message": "You successfully signed up!"
        })

class Login(Resource):
    
    def post(self):
        post_data = request.get_json()

        username = post_data["username"]
        password = post_data["password"]

        if not user_exist(username):
            return jsonify({"status": 401, "message": "User does not exist"})
        
        if not verify_password(username, password):
            return jsonify({
                "status": 302,
                "message": "Incorrect Password"
            })
        
        return jsonify({
            "status": 200,
            "message": "You successfully logged in!"
        })
        
class Detect(Resource):
    
    def post(self):
        post_data = request.get_json()

        username = post_data["username"]
        password = post_data["password"]
        text1 = post_data['text1']
        text2 = post_data["text2"]

        if not user_exist(username):
            return jsonify({
                "status": 301,
                "message": "Invalid Username"
            })
        
        correct_password = verify_password(username, password)
        if not correct_password:
            return jsonify({
                "status": 302,
                "message": "Incorrect Password"
            })
        
        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)

        ratio = text1.similarity(text2)

        return jsonify({
            "status": 200,
            "ratio": ratio,
            "message": "Similarity score calculated successfully"
        })
    

api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(Detect, '/detect')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
