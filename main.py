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

@app.route("/identify")
def identify():
    email=request.args.get("email")
    phoneNumber=request.args.get("phoneNumber")
    result=db.session.execute(
        db.select(Contact).where(or_(Contact.email == email, Contact.phoneNumber == phoneNumber))
    )

    contacts=result.scalars().all()
    if not contacts:
        new_contact = Contact(
            email=email,
            phoneNumber=phoneNumber,
            linkPrecedence='primary',
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
            deletedAt=None
        )
        db.session.add(new_contact)
        db.session.commit()

        return jsonify({
            "contact": {
                "primaryContactId": new_contact.id,
                "emails": [new_contact.email] if new_contact.email else [],
                "phoneNumbers": [new_contact.phoneNumber] if new_contact.phoneNumber else [],
                "secondaryContactIds": []
            }
        }), 200

if __name__ == '__main__':
    app.run(debug=True)

