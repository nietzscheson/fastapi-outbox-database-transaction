import json
import os
from datetime import datetime
from tkinter import EventType
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
from pydantic import Field
from pydantic_settings import BaseSettings
import factory
from factory.alchemy import SQLAlchemyModelFactory
import typer
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from debezium import DebeziumConnector

class Settings(BaseSettings):
    database_url: str = Field()

settings = Settings()

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

session = SessionLocal()


class Resource(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

class Author(Resource):
    __tablename__ = "authors"

    name = Column(String)


class Book(Resource):
    __tablename__ = "books"

    title = Column(String)
    author_id = Column(ForeignKey(Author.id), nullable=False)
    author = relationship("Author")


class Event(Resource):
    __tablename__ = "events"

    aggregatetype = Column(String(255), nullable=False)
    aggregateid = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow())



class AuthorFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Author
        sqlalchemy_session = session

    name = factory.Faker("first_name")

class BookFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Book
        sqlalchemy_session = session

    title = factory.Faker("first_name")
    author = factory.SubFactory(AuthorFactory)

app = typer.Typer()

@app.command()
def author():

    try:

        author = AuthorFactory.create()

        event = Event(aggregatetype="author", type="AuthorCreated", payload=json.dumps({"id": str(author.id), "name": author.name}))
        session.add(author)
        session.add(event)

        session.commit()

    except Exception as e:
        session.rollback()
        print(e)

@app.command()
def authors():

    try:
        for _ in range(10):
            author = AuthorFactory.create()

            event = Event(aggregatetype="author", type="AuthorCreated", payload=json.dumps({"id": str(author.id), "name": author.name}))
            session.add(author)
            session.add(event)

        session.commit()

    except Exception as e:
        session.rollback()
        print(e)

@app.command()
def book():

    try:

        book = BookFactory.create()

        event = Event(aggregatetype="book", type="BookCreated", payload=json.dumps({"id": str(book.id), "name": book.title }))
        session.add(book)
        session.add(event)

        session.commit()

    except Exception as e:
        session.rollback()
        print(e)

@app.command()
def debezium_route():

    transforms = {
        'transforms': 'route',
        'transforms.route.type': 'org.apache.kafka.connect.transforms.RegexRouter',
        'transforms.route.regex': '([^.]+)\\.([^.]+)\\.([^.]+)',
        'transforms.route.replacement': '$3'
    }

    try:
        connector = DebeziumConnector("http://localhost:8083/connectors/")
        response = connector.create_connector('route-cdc', transforms)

        print(response)

    except Exception as e:
        print(e)

@app.command()
def debezium_outbox():

    transforms = {
        "tombstones.on.delete" : "false",
        "transforms": "outbox",
        "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
        "transforms.outbox.route.topic.replacement": "${routedByValue}.events",
        "transforms.outbox.table.field.event.timestamp" : "timestamp",
        "transforms.outbox.table.fields.additional.placement" : "type:header:eventType",
    }

    try:
        connector = DebeziumConnector("http://localhost:8083/connectors/")
        response = connector.create_connector('outbox-cdc', transforms)

        print(response)

    except Exception as e:
        print(e)

if __name__ == "__main__":
    app()
