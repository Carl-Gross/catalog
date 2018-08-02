
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://catalog:fsbb231@localhost/catalog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from db_setup import Owner, Make, Model


# Create categories
make = Make(name="BMW")

db.session.add(make)
db.session.commit()

make = Make(name="Alfa Romeo")

db.session.add(make)
db.session.commit()

make = Make(name="Audi")

db.session.add(make)
db.session.commit()

make = Make(name="Porsche")

db.session.add(make)
db.session.commit()

make = Make(name="Chevy")

db.session.add(make)
db.session.commit()

make = Make(name="Nissan")

db.session.add(make)
db.session.commit()
