from flask import Flask, request
from random import choice

app = Flask(__name__)
app.json.ensure_ascii = False 

about_me = {
   "name": "Вадим",
   "surname": "Шиховцов",
   "email": "vshihovcov@specialist.ru"
}

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "rating": 3,
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "rating": 5,
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "author": "Mosher’s Law of Software Engineering",
       "rating": 4,
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "rating": 2,
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]

@app.route("/")
def hello_world():
   return "Hello, World!"


@app.route("/about")
def about():
   print(about_me)
   return about_me


@app.route("/quotes")
def all_quotes():
   return quotes

@app.route("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
   for quote in quotes:
        if quote.get("id") == quote_id:
           return quote_cnt
   return f"Quote with id={quote_id} not found", 404


@app.route("/quotes/count")
def quote_cnt():
   return {"count": len(quotes)} 

@app.route("/quotes/random_q")
def quote_random():
   return choice(quotes)


@app.route("/quotes", methods=['POST'])
def create_quote():
   new_quote = request.json
   last_quote = quotes[-1]
   new_id = last_quote["id"] + 1
   new_quote["rating"] = new_quote.get("rating") if "rating" in new_quote.keys() and new_quote.get("rating") <= 5 and new_quote.get("rating") >= 1 else 1
   new_quote["id"] = new_id
   quotes.append(new_quote)
   return new_quote, 201

@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
   new_data = request.json
   for quote in quotes:
      #print(quote["id"]== id)
      if quote.get("id") == id:
         #print("ok")
         quote["text"] = new_data.get("text") if "text" in new_data.keys() else quote.get("text")
         quote["author"] = new_data.get("author") if "author" in new_data.keys() else quote.get("author")
         quote["rating"] = new_data.get("rating") if "rating" in new_data.keys() and new_data.get("rating") <= 5 and new_data.get("rating") >= 1 else 1
         #print(quotes)
         return quote, 200
   return f"Quote with id={id} not found", 404


@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete(id):
   for quote in quotes:
      if quote.get("id") == id:
         quotes.remove(quote)
         print(quotes)
         return f"Quote with id {id} is deleted.", 200
   return f"Quote with id={id} not found", 404


@app.route('/quotes/filter', methods=['GET'])
def filter_quotes():
   args = request.args
   res = list()
   author = args.get("author", type = str)
   rating = args.get("rating", type = int)
   for quote in quotes:
      if (author == quote.get("author") or author is None) and (rating == quote.get("rating") or rating is None):
         res.append(quote)
   return res, 200 


if __name__ == "__main__":
   app.run(debug=True)