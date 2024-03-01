from flask import Flask, request, jsonify, abort
from random import choice
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / 'main.db'
print(BASE_DIR)
print(DATABASE)
app = Flask(__name__)
app.json.ensure_ascii = False 

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATABASE}"
app.config['SQLALCHEMYpython -m pip uninstall_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class QuoteModel(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   author = db.Column(db.String(32), unique=False)
   text = db.Column(db.String(255), unique=False)

   def __init__(self, author, text):
       self.author = author
       self.text  = text

#обработка ошибок и возврат их в JSON
@app.errorhandler(HTTPException)
def handle_exception(e):
   return jsonify({"message": e.description}), e.code

@app.route("/quotes")
def all_quotes():
   conn = get_db()
   cursor = conn.cursor()
   select_quotes = "Select id, author, text from quotes;"
   cursor.execute(select_quotes)
   quotes_db = cursor.fetchall()
   keys = ["id", "author", "text"]
   # quotes = [dict(zip(keys, quote_db)) for quote_db in quotes_db]
   quotes = []
   for quote_db in quotes_db:
      quote = dict(zip(keys, quote_db))
      quotes.append(quote)

   return jsonify(quotes)

@app.route("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
   conn = get_db()
   cursor = conn.cursor()
   select_quote = f"Select id, author, text from quotes where id = {quote_id};"
   #print(select_quote)
   cursor.execute(select_quote)
   quote_db = cursor.fetchone()
   keys = ["id", "author", "text"]
   if quote_db is not None:
      #print(dict(zip(keys, quote_db)))
      return  jsonify(dict(zip(keys, quote_db)))
   abort(404, f"Quote with id={quote_id} not found")
   #return f"Quote with id={quote_id} not found", 404



@app.route("/quotes", methods=['POST'])
def create_quote():
   new_quote = request.json
   conn = get_db()
   cursor = conn.cursor()
   #new_quote["rating"] = new_quote.get("rating") if "rating" in new_quote.keys() and new_quote.get("rating") <= 5 and new_quote.get("rating") >= 1 else 1
   insert_quote = f"insert into quotes(author, text) values(?, ?);"
   #print(insert_quote)
   cursor.execute(insert_quote, (new_quote['author'], new_quote['text']))
   new_quote["id"] = cursor.lastrowid
   #print(row_id)
   conn.commit()
   return jsonify(new_quote), 201

@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
   new_data = request.json
   conn = get_db()
   cursor = conn.cursor()
   update_quote = f"""update quotes 
     set author = case when '{new_data.get("author")}' == 'None' then author else '{new_data.get("author")}' end, 
     text =  case when '{new_data.get("text")}' == 'None' then text else '{new_data.get("text")}' end
     where id = {id};"""
   #print(update_quote)
   cursor.execute(update_quote)
   conn.commit()
   quote_db = f"select id, author, text from quotes where id = {id};"
   cursor.execute(quote_db)
   quote = cursor.fetchone()
   keys = ["id", "author", "text"]
   if quote is not None:
      #print(dict(zip(keys, quote_db)))
      return  jsonify(dict(zip(keys, quote))), 200
   abort(404, f"Quote with id={id} not found")
   #return f"Quote with id={id} not found", 404


@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete(id):
   conn = get_db()
   cursor = conn.cursor()
   update_quote = f"""delete from quotes where id = {id} ;"""
   cursor.execute(update_quote)
   cnt = cursor.rowcount
   conn.commit()
   if cnt > 0:
      return f"Quote with id {id} is deleted.", 200
   abort(404, f"Quote with id={id} not found")
   #return f"Quote with id={id} not found", 404



if __name__ == "__main__":
   app.run(debug=True)