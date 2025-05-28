from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime,or_

app = Flask(__name__)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contact.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Contact(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phoneNumber: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    linkedId: Mapped[int] = mapped_column(Integer, nullable=True, foreign_key=True)
    linkPrecedence: Mapped[str] = mapped_column(String)
    createdAt: Mapped[datetime] = mapped_column(DateTime)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    deletedAt: Mapped[datetime] = mapped_column(DateTime, nullable=True)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)
