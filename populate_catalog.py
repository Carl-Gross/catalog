from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from db_setup import User, Make, Model

engine = create_engine('sqlite:///catalog_project.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance

Base = declarative_base()

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create categories
make = Make(name="BMW")

session.add(make)
session.commit()

make = Make(name="Alfa Romeo")

session.add(make)
session.commit()

make = Make(name="Audi")

session.add(make)
session.commit()

make = Make(name="Porsche")

session.add(make)
session.commit()

make = Make(name="Chevy")

session.add(make)
session.commit()

make = Make(name="Nissan")

session.add(make)
session.commit()