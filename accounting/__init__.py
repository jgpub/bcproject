#You will need to pip install flask and the sqlalchemy extension for flask.
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

# Initialize the application.
app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

# Import the views file for view routing.
import views

# Import the endpoints file for end point routing.
import endpoints