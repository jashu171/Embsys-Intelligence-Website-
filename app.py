from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/chat")
def chat():
    """Redirect to the chatbot application"""
    return redirect("http://localhost:8000", code=302)


@app.route("/start-free")
def start_free():
    """Handle the 'Start for Free' button click"""
    return redirect("http://localhost:8000", code=302)

 
if __name__ == "__main__":
    app.run(debug=True, port=5005)
