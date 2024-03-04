from flask import Flask, request, jsonify, abort
from random import choice
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, insert, update, or_, func
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / 'quotes.db'

app = Flask(__name__)
app.json.ensure_ascii = False 

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
     
class AuthorModel(db.Model):
   __tablename__ = "authors"
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(32), nullable=False)
   surname = db.Column(db.String(64))
   is_deleted = db.Column(db.Boolean(), nullable=False, default = False, server_default=db.sql.false())
   quotes = db.relationship('QuoteModel', backref='author', lazy='dynamic', cascade="all, delete-orphan")

   def __init__(self, name, surname):
      self.surname = surname
      self.name = name
      self.is_deleted = 0
      

   def to_dict(self):
      return {
         "id": self.id,
         "name": self.name,
         "surname": self.surname
      }
   
   def __repr__(self):
      return f"Author({self.name},{self.surname})"
   
class QuoteModel(db.Model):
   __tablename__ = "quotes"
   id = db.Column(db.Integer, primary_key=True)
   author_id = db.Column('author_id', db.Integer, db.ForeignKey(AuthorModel.id))
   _text = db.Column('text', db.String(255), unique=False)
   _rating = db.Column('rating', db.Integer, nullable=False, default = 1, server_default = text("1"))
   created = db.Column(db.DateTime(timezone=True), server_default=func.now())

   def __init__(self, author, text, rating=None):
       self.author_id = author.id
       self._text  = text
       self._rating  = rating if rating in range(1,6) else 1

   def __repr__(self):
      return f"Quote({self.author.name}, {self._text}, {self._rating}, {self.created})"
   
   def to_dict(self):
      return {
         "id": self.id,
         "author": self.author.to_dict(),
         "text": self._text,
         "rating": self._rating,
         "created": self.created.strftime('%d.%m.%Y')
      }
   
   @property
   def text(self):
      return self._text

   @text.setter
   def text(self, text_new):
      if text_new is not None:
         self._text = text_new

   @property
   def rating(self):
      return self._rating

   @rating.setter
   def rating(self, rating_new):
      if rating_new is not None and rating_new in range(1, 6):
         self._rating = rating_new
      elif self._rating is None:
         self._rating = 1




#обработка ошибок и возврат их в JSON
@app.errorhandler(HTTPException)
def handle_exception(e):
   return jsonify({"message": e.description}), e.code



@app.route("/authors")
def all_authors():
   authors_db = AuthorModel.query.filter(AuthorModel.is_deleted == False).all()
   authors_gen = (a.to_dict() for a in authors_db) 
   authors = []
   for i in authors_gen:
      authors.append(i)
   return jsonify(authors), 200

@app.route("/authors/<int:author_id>")
def author_by_id(author_id):
   author_db = AuthorModel.query.filter(AuthorModel.is_deleted == False, AuthorModel.id == author_id).one_or_none()
   if author_db is None:
      abort(404, f"Author with id={author_id} not found")
   print(author_db)
   author = author_db.to_dict()
   return  jsonify(author)

@app.route("/authors_del")
def all_del_authors():
   authors_db = AuthorModel.query.filter(AuthorModel.is_deleted == True).all()
   authors_gen = (a.to_dict() for a in authors_db) 
   authors = []
   for i in authors_gen:
      authors.append(i)
   return jsonify(authors), 200

@app.route("/authors", methods=['POST'])
def create_author():
      author_data = request.json
      author = AuthorModel(author_data.get("name"), author_data.get("surname"))
      db.session.add(author)
      db.session.commit()
      return author.to_dict(), 201

@app.route('/authors/filter', methods=['GET'])
def filter_authors():
   args = request.args
   author_name = args.get("name", type = str)
   author_surname = args.get("surname", type = str)
   authors_db = AuthorModel.query.filter(or_(func.lower(AuthorModel.name)==func.lower(author_name), func.lower(AuthorModel.surname) == func.lower(author_surname)), AuthorModel.is_deleted == False).all()
   authors_gen = (a.to_dict() for a in authors_db) 
   authors = []
   for i in authors_gen:
      authors.append(i)
   return jsonify(authors), 200
   

@app.route("/authors/<int:author_id>", methods=['PUT'])
def edit_author(author_id):
   new_data = request.json
   author_db = AuthorModel.query.filter(AuthorModel.is_deleted == False, AuthorModel.id == author_id).one_or_none()
   if author_db is None:
      abort(404, f"Author with id={author_id} not found")
   for key, value in new_data.items():
      setattr(author_db, key, value)
   db.session.add(author_db)
   db.session.commit()
   author_new_db = AuthorModel.query.get(author_id)
   author = author_new_db.to_dict()
   return jsonify(author), 200

@app.route("/authors/delete/<int:author_id>", methods=['PUT'])
def delete_author(author_id):
   author_db = AuthorModel.query.filter(AuthorModel.is_deleted == False, AuthorModel.id == author_id).one_or_none()
   if author_db is None:
      abort(404, f"Author with id={author_id} not found")
   author_db.is_deleted = True
   db.session.add(author_db)
   #db.session.delete(author_db)  
   db.session.commit() 
   return jsonify(f"Author with id {author_id} is deleted."), 200

@app.route("/authors/restore/<int:author_id>", methods=['PUT'])
def restore_author(author_id):
   author_db = AuthorModel.query.filter(AuthorModel.is_deleted == True, AuthorModel.id == author_id).one_or_none()
   if author_db is None:
      abort(404, f"Author with id={author_id} not found")
   author_db.is_deleted = False
   db.session.add(author_db)
   #db.session.delete(author_db)  
   db.session.commit() 
   return jsonify(f"Author with id {author_id} is restored."), 200

@app.route("/quotes")
def all_quotes():
   quotes_db = QuoteModel.query.all()
   quotes_gen = (q.to_dict() for q in quotes_db) 
   quotes = []
   for i in quotes_gen:
      quotes.append(i)
   return jsonify(quotes), 200

@app.route("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
   quote_db = QuoteModel.query.get(quote_id)
   if quote_db is None:
      abort(404, f"Quote with id={quote_id} not found")
   print(quote_db)
   quote = quote_db.to_dict()
   return  jsonify(quote)

@app.route("/authors/<int:author_id>/quotes")
def quoty_by_author(author_id):
   quotes_db = QuoteModel.query.filter(QuoteModel.author_id == author_id).all()
   quotes_gen = (q.to_dict() for q in quotes_db) 
   quotes = []
   for i in quotes_gen:
      quotes.append(i)
   return jsonify(quotes), 201

@app.route("/authors/<int:author_id>/quotes", methods=['POST'])
def create_quote(author_id):
   author = AuthorModel.query.get(author_id)
   if author is None:
      abort(404, f"Author with id={author_id} not found")
   new_quote = request.json
   print(author)
   print(new_quote)
   q = QuoteModel(author, new_quote.get("text"), new_quote.get("rating"))
   db.session.add(q)
   db.session.commit()
   print(q)
   return jsonify(q.to_dict()), 201

@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
   new_data = request.json
   quote_db = QuoteModel.query.get(quote_id)
   if quote_db is None:
      abort(404, f"Quote with id={quote_id} not found")
   for key, value in new_data.items():
      setattr(quote_db, key, value)
   db.session.add(quote_db)
   db.session.commit()
   quote_new_db = QuoteModel.query.get(quote_id)
   quote = quote_new_db.to_dict()
   return jsonify(quote), 200
   


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
   quote_db = QuoteModel.query.get(quote_id)
   if quote_db is None:
      abort(404, f"Quote with id={quote_id} not found")
   db.session.delete(quote_db)  
   db.session.commit() 
   return jsonify(f"Quote with id {quote_id} is deleted."), 200


@app.route('/quotes/filter', methods=['GET'])
def filter_quotes():
   args = request.args
   author = args.get("name", type = str)
   rating = args.get("rating", type = int)
   quotes_db = QuoteModel.query.filter(or_(QuoteModel.author.has(name = author), QuoteModel.rating == rating)).all()
   quotes_gen = (q.to_dict() for q in quotes_db) 
   quotes = []
   for i in quotes_gen:
      quotes.append(i)
   return jsonify(quotes), 200

@app.route("/quotes/<int:quote_id>/rating_plus")
def rating_plus(quote_id):
   quote_db = QuoteModel.query.get(quote_id)
   if quote_db is None:
      abort(404, f"Quote with id={quote_id} not found")
   quote_db.rating = quote_db.rating + 1
   db.session.add(quote_db)
   db.session.commit() 
   return  jsonify(quote_db.to_dict()), 200

@app.route("/quotes/<int:quote_id>/rating_minus")
def rating_minus(quote_id):
   quote_db = QuoteModel.query.get(quote_id)
   if quote_db is None:
      abort(404, f"Quote with id={quote_id} not found")
   quote_db.rating = quote_db.rating - 1
   db.session.add(quote_db)
   db.session.commit() 
   return  jsonify(quote_db.to_dict()), 200

if __name__ == "__main__":
   app.run(debug=True)