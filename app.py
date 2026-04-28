import os
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Input, Output, callback
import dash
from flask import Flask
from extensions import db, bcrypt, User, login_manager
import secrets

server = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db") 
server.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
server.config['SECRET_KEY'] = secrets.token_hex(16)

db.init_app(server)
bcrypt.init_app(server)
login_manager.init_app(server)
login_manager.login_view = "/"

app = Dash(__name__, server = server, use_pages = True, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True
)

app.layout = html.Div(
    [
        # Global theme state
        dcc.Store(id = "theme-store", data = "light"),

        # Theme stylesheet switcher
        html.Link(
            id = "theme-link",
            rel = "stylesheet",
            href = dbc.themes.BOOTSTRAP
        ),

        dash.page_container,
    ]
)

with server.app_context():
    db.create_all()



if __name__ == '__main__':
    app.run(debug = True)



@callback(
    Output("theme-link", "href"),
    Output("theme-store", "data"),
    Input("theme-toggle", "value"),
)
def toggle_theme(is_dark):
    if is_dark:
        return dbc.themes.DARKLY, "dark"
    return dbc.themes.BOOTSTRAP, "light"

