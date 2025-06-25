#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url")
        bio = data.get("bio")

        try:
            user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            user.password_hash = password

            db.session.add(user)
            db.session.commit()

            session["user_id"] = user.id

            return jsonify({
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"errors": ["Username must be unique."]}), 422
        except Exception as e:
            db.session.rollback()
            return jsonify({"errors": [str(e)]}), 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if user_id:
            user = User.query.get(user_id)
            if user:
                return jsonify({
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio
                }), 200
        return jsonify({"error": "Unauthorized"}), 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            return jsonify({
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }), 200

        return jsonify({"error": "Unauthorized"}), 401

class Logout(Resource):
    def delete(self):
        if session.get("user_id"):
            session["user_id"] = None
            return {}, 204
        return jsonify({"error": "Unauthorized"}), 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        recipes = Recipe.query.all()
        return jsonify([recipe.to_dict() for recipe in recipes]), 200

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes_to_complete = data.get("minutes_to_complete")

        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )

            # 🔥 Force validators to run and catch ValueErrors before commit
            db.session.add(recipe)
            db.session.flush()
            db.session.commit()

            return jsonify(recipe.to_dict()), 201

        except ValueError as ve:
            db.session.rollback()
            return jsonify({"errors": [str(ve)]}), 422

        except Exception as e:
            db.session.rollback()
            return jsonify({"errors": [str(e)]}), 422

# Register resources
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
