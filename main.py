from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime,or_
import os

app = Flask(__name__)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
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

    existing_emails = {c.email for c in contacts if c.email}
    existing_phones = {c.phoneNumber for c in contacts if c.phoneNumber}

    new_email = email and email not in existing_emails
    new_phone = phoneNumber and phoneNumber not in existing_phones

    if contacts and (new_email or new_phone):
        primary_contacts = [c for c in contacts if c.linkPrecedence == 'primary']
        primary_contact = min(primary_contacts, key=lambda c: c.createdAt) if primary_contacts else min(contacts,
                                                                                                        key=lambda
                                                                                                            c: c.createdAt)

        new_secondary = Contact(
            email=email,
            phoneNumber=phoneNumber,
            linkedId=primary_contact.id,
            linkPrecedence='secondary',
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
            deletedAt=None
        )
        db.session.add(new_secondary)
        db.session.commit()

        contacts.append(new_secondary)
    primary_contacts = [c for c in contacts if c.linkPrecedence == 'primary']
    primary_contact = min(primary_contacts, key=lambda c: c.createdAt) if primary_contacts else min(contacts, key=lambda
        c: c.createdAt)

    for contact in primary_contacts:
        if contact.id != primary_contact.id:
            contact.linkPrecedence = 'secondary'
            contact.linkedId = primary_contact.id
            contact.updatedAt = datetime.utcnow()
            db.session.add(contact)

    db.session.commit()

    all_linked_contacts = db.session.execute(
        db.select(Contact).where(
            or_(
                Contact.id == primary_contact.id,
                Contact.linkedId == primary_contact.id,
                Contact.id.in_([c.linkedId for c in contacts if c.linkedId])
            )
        )
    ).scalars().all()

    all_linked_contacts = list({c.id: c for c in all_linked_contacts}.values())

    emails = []
    phoneNumbers = []
    secondary_ids = []

    for contact in all_linked_contacts:
        if contact.email and contact.email not in emails:
            emails.append(contact.email)
        if contact.phoneNumber and contact.phoneNumber not in phoneNumbers:
            phoneNumbers.append(contact.phoneNumber)
        if contact.linkPrecedence == 'secondary':
            secondary_ids.append(contact.id)

    if primary_contact.email in emails:
        emails.remove(primary_contact.email)
        emails.insert(0, primary_contact.email)
    if primary_contact.phoneNumber in phoneNumbers:
        phoneNumbers.remove(primary_contact.phoneNumber)
        phoneNumbers.insert(0, primary_contact.phoneNumber)

    return jsonify({
        "contact": {
            "primaryContactId": primary_contact.id,
            "emails": emails,
            "phoneNumbers": phoneNumbers,
            "secondaryContactIds": secondary_ids
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
