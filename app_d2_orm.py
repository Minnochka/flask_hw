from flask import Flask, request, jsonify, abort
from random import choice
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, insert, update, or_
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / 'main.db'
app = Flask(__name__)
app.json.ensure_ascii = False 

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class QuoteModel(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   _author = db.Column('author', db.String(32), unique=False)
   _text = db.Column('text', db.String(255), unique=False)
   _rating = db.Column('rating', db.Integer, unique=False, default = 1, server_default = text("1"))

   def __init__(self, author, text, rating=None):
       self._author = author
       self._text  = text
       self._rating  = rating if rating in range(1,6) else 1

   def __repr__(self):
      return f"Quote({self._author}, {self._text}, {self._rating})"
   
   def to_dict(self):
      return {
         "id": self.id,
         "author": self._author,
         "text": self._text,
         "rating": self._rating
      }
   
   @property
   def author(self):
      return self._author
   
   @author.setter
   def author(self, author_new):
      if author_new is not None:
         self._author = author_new

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
      if rating_new is not None:
         self._rating = rating_new
      

#обработка ошибок и возврат их в JSON
@app.errorhandler(HTTPException)
def handle_exception(e):
   return jsonify({"message": e.description}), e.code

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



@app.route("/quotes", methods=['POST'])
def create_quote():
   new_quote = request.json
   #quote_for_db = QuoteModel(*new_quote)
   #quotes_db = db.session.scalars(insert(QuoteModel).returning(QuoteModel),new_quote)
   quote_for_db = QuoteModel(new_quote.get("author"), new_quote.get("text"), new_quote.get("rating"))
   print(quote_for_db)
   db.session.add(quote_for_db)
   db.session.flush()
   db.session.refresh(quote_for_db)
   db.session.commit()
   quote = quote_for_db.to_dict()
   return jsonify(quote), 201

@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
   new_data = request.json
   quote_db = QuoteModel.query.get(quote_id)
   if quote_db is None:
      abort(404, f"Quote with id={quote_id} not found")
   #quote_db.author = new_data.get("author")
   #quote_db.text = new_data.get("text")
   #quote_db.rating = new_data.get("rating")
   #stmt = update(QuoteModel).where(QuoteModel.id==quote_id).returning(QuoteModel)
   #print('-----------------------------------------------------------------------------------------------------------------------------')
   #print(stmt)
   #quote_new_db = db.session.scalars(update(QuoteModel).where(QuoteModel.id==quote_id).returning(QuoteModel),quote_db.to_dict())
   for key, value in new_data.items():
      setattr(quote_db, key, value)
   db.session.add(quote_db)
   db.session.commit()
   quote_new_db = QuoteModel.query.get(quote_id)
   quote = quote_new_db.to_dict()
   return jsonify(quote), 200
   


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete(quote_id):
   quote_db = QuoteModel.query.get(quote_id)
   if quote_db is None:
      abort(404, f"Quote with id={quote_id} not found")
   db.session.delete(quote_db)  
   db.session.commit() 
   return f"Quote with id {quote_id} is deleted.", 200


@app.route('/quotes/filter', methods=['GET'])
def filter_quotes():
   args = request.args
   author = args.get("author", type = str)
   rating = args.get("rating", type = int)
   quotes_db = QuoteModel.query.filter(or_(QuoteModel.author.lower==author.lower, QuoteModel.rating == rating)).all()
   quotes_gen = (q.to_dict() for q in quotes_db) 
   quotes = []
   for i in quotes_gen:
      quotes.append(i)
   return jsonify(quotes), 200


if __name__ == "__main__":
   app.run(debug=True)