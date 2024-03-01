from flask import Flask, request, jsonify, abort, g
from random import choice
from pathlib import Path
import sqlite3
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__name__).parent
DATABASE = BASE_DIR / "test.db"

app = Flask(__name__)
app.json.ensure_ascii = False 

#обработка ошибок и возврат их в JSON
@app.errorhandler(HTTPException)
def handle_exception(e):
   return jsonify({"message": e.description}), e.code

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/quotes")
def all_quotes():
   conn = get_db()
   cursor = conn.cursor()
   select_quotes = "Select id, author, text from quotes;"
   cursor.execute(select_quotes)
   quotes_db = cursor.fetchall()
   keys = ["id", "author", "text"]
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
   cursor.execute(select_quote)
   quote_db = cursor.fetchone()
   keys = ["id", "author", "text"]
   if quote_db is not None:
      return  jsonify(dict(zip(keys, quote_db)))
   abort(404, f"Quote with id={quote_id} not found")



@app.route("/quotes", methods=['POST'])
def create_quote():
   new_quote = request.json
   conn = get_db()
   cursor = conn.cursor()
   #new_quote["rating"] = new_quote.get("rating") if "rating" in new_quote.keys() and new_quote.get("rating") <= 5 and new_quote.get("rating") >= 1 else 1
   insert_quote = f"insert into quotes(author, text) values(?, ?);"
   cursor.execute(insert_quote, (new_quote['author'], new_quote['text']))
   new_quote["id"] = cursor.lastrowid
   conn.commit()
   return jsonify(new_quote), 201

@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
   new_data = request.json
   conn = get_db()
   cursor = conn.cursor()
   #update_quote = f"""update quotes 
   #  set author = case when '{new_data.get("author")}' == 'None' then author else '{new_data.get("author")}' end, 
   #  text =  case when '{new_data.get("text")}' == 'None' then text else '{new_data.get("text")}' end
   #  where id = {id};"""
   #print(update_quote)
   update_quote = f"""update quotes 
     set author ?, 
     text =  ?
     where id = ?;"""
   cursor.execute(update_quote, (*new_data, id))
   conn.commit()
   quote_db = f"select id, author, text from quotes where id = {id};"
   cursor.execute(quote_db)
   quote = cursor.fetchone()
   keys = ["id", "author", "text"]
   if quote is not None:
      return  jsonify(dict(zip(keys, quote))), 200
   abort(404, f"Quote with id={id} not found")


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



if __name__ == "__main__":
   app.run(debug=True)