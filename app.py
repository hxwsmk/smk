from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from datetime import timedelta
from flask_cors import CORS

# Inițializăm aplicația
app = Flask(__name__)
CORS(app)

# Configurare bază de date
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'  # folosește doar una
app.config['JWT_SECRET_KEY'] = 'super-secret'  # schimbă cu o cheie mai sigură în producție
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Inițializare extensii
db = SQLAlchemy(app)
jwt = JWTManager(app)

# MODELE
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)

# Creăm tabelele la pornire
with app.app_context():
    db.create_all()

# Pagină test
@app.route('/')
def home():
    return '✅ Serverul Flask funcționează'

# REGISTER
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "User already exists"}), 400
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

# LOGIN
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if not user:
        return jsonify({"msg": "Bad credentials"}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token}), 200

# NOTES
@app.route('/notes', methods=['GET', 'POST'])
@jwt_required()
def notes():
    user_id = int(get_jwt_identity())
    if request.method == 'POST':
        data = request.get_json()
        new_note = Note(user_id=user_id, content=data['content'])
        db.session.add(new_note)
        db.session.commit()
        return jsonify({"msg": "Note added"}), 201
    else:
        notes = Note.query.filter_by(user_id=user_id).all()
        return jsonify([{"id": n.id, "content": n.content} for n in notes]), 200

# DELETE NOTE
@app.route('/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"msg": "Note not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"msg": "Note deleted"}), 200

# Pentru rulare locală
if __name__ == '__main__':
    app.run(debug=True)
