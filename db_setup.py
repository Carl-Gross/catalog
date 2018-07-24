import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Make(Base):
    __tablename__ = 'make'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
        }


class Model(Base):
    __tablename__ = 'model'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    make_id = Column(Integer, ForeignKey('make.id'))
    make = relationship(Make)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    last_update = Column(String(250))


# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'make_id': self.make_id,
            'user_id': self.user_id,
            'last_update': self.last_update
        }


engine = create_engine('sqlite:///catalog_project.db')

Base.metadata.create_all(engine)