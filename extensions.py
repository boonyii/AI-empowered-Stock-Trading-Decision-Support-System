from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False, unique = True)
    password = db.Column(db.String(80), nullable = False)
    balance = db.Column(db.Float, default = 0.0)
    holdings = db.relationship('StockHolding', backref = 'owner', lazy = True)

class StockHolding(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    ticker = db.Column(db.String(10), nullable = False)     
    shares = db.Column(db.Float, nullable = False)          
    avg_price = db.Column(db.Float, nullable = False)       
    total_value = db.Column(db.Float, nullable = False) 

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    ticker = db.Column(db.String(20), nullable = False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "ticker", name = "unique_user_watchlist"),
    )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))