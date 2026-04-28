from dash import Dash, html, dcc, Input, Output, no_update, State, register_page, callback, ctx, ALL
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from google.genai import types
from chatbot import generate_once
from lstm import lstm_model
from extensions import db, bcrypt, User, StockHolding, Watchlist
from flask_login import login_user, current_user
from xgboostt import xgboost_model
from svm import svm_model
from randomforest_classifier import rf_model
from stock_utils import fetch_stock_data, process_data, calculate_metrics, add_technical_indicators

register_page(__name__, path="/")



fig = make_subplots(rows = 1, cols = 1)
    
# App layout
navbar = dbc.Navbar(
    dbc.Container([
        
        dbc.NavbarBrand(
            "MarketLens",
            className="fw-bold",
            style={"fontSize": "2rem"}
        ),

        # Hamburger button (shows when collapsed) 
        dbc.NavbarToggler(id="nav-toggler", n_clicks=0),

        dbc.Collapse(
            [
            # Center controls 
                dbc.Nav(
                    [
                        dbc.InputGroup(
                            [
                                dbc.InputGroupText(
                                    html.I(className="bi bi-search"),
                                    style={"backgroundColor": "white"},
                                ),
                                dbc.Input(
                                    id="ticker",
                                    type="text",
                                    value="AAPL",
                                    placeholder="Search",
                                    style={"borderLeft": "0"},
                                ),
                            ],
                            style={"width": "110px", "height": "36px"},
                        ),

                        dcc.Dropdown(
                            id="time-period",
                            options=[
                                {"label": "1D", "value": "1d"},
                                {"label": "1M", "value": "1mo"},
                                {"label": "1Y", "value": "1y"},
                                {"label": "All", "value": "max"},
                            ],
                            value="1d",
                            clearable=False,
                            style={"width": "60px"},
                        ),

                        dcc.Dropdown(id="interval", clearable=False, style={"width": "60px"}),

                        dcc.Dropdown(
                            id="chart-type",
                            options=["Candlestick", "Line"],
                            value="Candlestick",
                            clearable=False,
                            style={"width": "130px"},
                        ),

                        dbc.DropdownMenu(
                            label=html.Span(
                                [
                                    html.I(className="bi bi-graph-up me-2"),
                                    "Indicators",
                                ],
                                style={
                                    "fontSize": "1.1rem",
                                    "fontWeight": "500",
                                    "color": "white",
                                },
                            ),
                            children=[
                                html.Div(
                                    dbc.Checklist(
                                        id="technical-indicators",
                                        options=[
                                            {"label": "SMA 20", "value": "SMA 20"},
                                            {"label": "EMA 20", "value": "EMA 20"},
                                            {"label": "WMA 20", "value": "WMA 20"},
                                            {"label": "KAMA", "value": "KAMA"},
                                            {"label": "RSI", "value": "RSI"},
                                        ],
                                        value=[],
                                        className="px-3",
                                    ),
                                    style={
                                        "height": "80px",
                                        "overflowY": "auto"
                                    },
                                )
                            ],
                            nav=True,
                            in_navbar=True,
                        ),

                        dbc.DropdownMenu(
                            label=html.Span(
                                [
                                    html.I(className="bi bi-hammer me-2"),
                                    "AI Tools",
                                ],
                                style={
                                    "fontSize": "1.1rem",
                                    "fontWeight": "500",
                                    "color": "white",
                                },
                            ),
                            children=[
                                dbc.DropdownMenuItem("LSTM", id="LSTM", n_clicks=0),
                                dbc.DropdownMenuItem("XGBoost", id="XGBoost", n_clicks=0),
                                dbc.DropdownMenuItem("SVM", id="SVM", n_clicks=0),
                                dbc.DropdownMenuItem("Random Forest", id="randomforest", n_clicks=0),
                            ],
                            nav=True,
                            in_navbar=True,
                        ),
                    ],
                    className="mx-auto gap-2",
                    style={"marginLeft": "100px"},
                    navbar=True,
                ),

                # Right controls
                dbc.Nav(
                    [
                        dbc.NavItem(
                            html.Div(
                                [
                                    html.I(
                                        className="bi bi-sun-fill me-2",
                                        style={"color": "#FFD43B", "fontSize": "1.1rem"},
                                    ),

                                    dbc.Switch(
                                        id="theme-toggle",
                                        value=False,   # False = Light, True = Dark
                                        persistence=True,
                                        className="mb-0",
                                    ),

                                    html.I(
                                        className="bi bi-moon-fill ms-0",
                                        style={"color": "#E0E0E0", "fontSize": "1.0rem"},
                                    ),
                                ],
                                className="d-flex align-items-center",
                            )
                        ),

                        dbc.NavItem([
                            dbc.NavLink(
                                [
                                    html.I(className="bi bi-person-circle me-2", style={"fontSize": "1.1rem", "fontWeight": "500", "color": "white"}), 
                                    html.Span("Login", id="login-text", style={"fontSize": "1.1rem", "fontWeight": "500", "color": "white"}) 
                                ],
                                id="login-toggle", 
                                n_clicks=0, 
                                href="/"
                                )
                        ]
                        )
                    ],
                    className="ms-auto d-flex align-items-center gap-4",
                    navbar=True,
                ),
            ],
            id="nav-collapse",
            is_open=False,  
            navbar=True,
            style={"paddingLeft": "100px"}
        ),
    ], fluid=True, style={"paddingLeft": "80px"}),
    id="main-navbar",
    sticky="top",
    color="#4F46E5", #4F46E5 / 0EA5E9
    expand="md"
)


layout = html.Div([
    navbar, 

    dbc.Container([
        dcc.Location(id="router", refresh=True),
        dcc.Store(id="watchlist-update-signal", data=0),
        dbc.Modal([ 
            dbc.ModalHeader("Long Short-Term Memory (LSTM) Results"),
            dbc.ModalBody(
                dbc.Spinner([
                    dcc.Graph(
                        id = "lstm-graphs-1",
                        figure = fig,
                    ),
                    dcc.Graph(
                        id = "lstm-graphs-2",
                        figure = fig,
                    ),
                    dcc.Graph(
                        id = "lstm-graphs-3",
                        figure = fig,
                    ),
                    dcc.Graph(
                        id = "lstm-graphs-4",
                        figure = fig,
                    )
                ], spinner_style={"position": "fixed", "top": "50%"}
                )
            )
        ],
        id = "lstm-modal",
        is_open = False,
        scrollable = True,
        size = "xl",
        fullscreen=False
        ),
        dcc.Store(id="lstm-cache", data={}),

        dbc.Modal([ 
            dbc.ModalHeader("XGBoost Results"),
            dbc.ModalBody(
                dbc.Spinner([
                    html.Div(id="xgboost-results-text", className="text-center"), # text-center ensures the summary stacks in the middle like the SVM modal
                    dcc.Graph(
                        id="xgboost-graph",
                        figure=fig,
                    ),
                ], spinner_style={"position": "fixed", "top": "30%"})
            )
        ],
        id="xgboost-modal",
        is_open=False,
        scrollable=True,
        size="xl",
        fullscreen=False
        ),
        dcc.Store(id="xgboost-cache", data={}),

        dbc.Modal([ 
            dbc.ModalHeader("Support Vector Machine (SVM) Results"),
            dbc.ModalBody(
                dbc.Spinner([
                    dcc.Graph(
                        id = "svm-graph",
                        figure = fig,
                    ),
                ], spinner_style={"position": "fixed", "top": "30%"}
                )
            )
        ],
        id = "svm-modal",
        is_open = False,
        scrollable = True,
        size = "xl",
        fullscreen=False
        ),
        dcc.Store(id="svm-cache", data={}),

        dbc.Modal([ 
            dbc.ModalHeader("Random Forest Results"),
            dbc.ModalBody(
                dbc.Spinner([
                    html.Div(id="rf-results"),
                ], spinner_style={"position": "fixed", "top": "30%"}
                )
            )
        ],
        id = "rf-modal",
        is_open = False,
        scrollable = True,
        size = "xl",
        fullscreen=False
        ),
        dcc.Store(id="rf-cache", data={}),
        
        dbc.Row([
            
            ############################## CHART SECTION: ##############################
            dbc.Col([ 
                dcc.Graph(
                id = "price-chart",
                figure = fig,
                style = {"height": "800px", "width": "100%", "marginTop": "20px"}
                ),
            dcc.Interval(
                id="live-interval",
                interval=60000,  # default, will be overwritten by callback
                n_intervals=0
                )
            ], style={"flex": "1 1 0", "minWidth": 0}   # allows chart to shrink
            ),
            ############################## USER SECTION: ###############################
            dbc.Col([
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Watchlist", className="mb-2 fw-semibold"),

                            html.Div(
                                id="watchlist-items",
                                className="d-flex flex-column gap-1",
                                style={
                                    "height": "300px",
                                    "overflowY": "auto",
                                    "paddingRight": "6px",
                                    
                                },
                            ),
                        ]
                    ),
                    className="border-0",
                    id="watchlist-card-container",
                    style={
                        "borderRadius": "16px",
                        "marginBottom": "12px",
                        "marginTop": "20px",
                        
                    },
                ),
                dbc.Card(
                    dbc.CardBody(
                        [

                            ############################## MAIN METRIC ##############################
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(id="main-metric"),
                                            className="border-0 h-100",
                                        ),
                                        width=12,
                                    )
                                ],
                                className="g-2",
                                style={"marginBottom": "12px"},
                            ),

                            ############################## HIGH / LOW / VOLUME ##############################
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card(dbc.CardBody(id="close-metric"), className="border-0 h-100"),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.Card(dbc.CardBody(id="high-metric"), className="border-0 h-100"),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.Card(dbc.CardBody(id="low-metric"), className="border-0 h-100"),
                                        width=4,
                                    ),
                                ],
                                className="g-2",
                                style={"marginBottom": "12px"},
                            ),

                            ############################## OPEN / CLOSE ##############################
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card(dbc.CardBody(id="open-metric"), className="border-0 h-100"),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.Card(dbc.CardBody(id="volume-metric"), className="border-0 h-100"),
                                        
                                    ),
                                ],
                                className="g-2",
                            ),
                        ],
                        className="p-3",
                    ),
                    id="main-card-container",
                    className="border-0 shadow-sm",
                    style={
                        "borderRadius": "16px",
                    },
                ),

                html.Hr(),
                
                dbc.Row([   
                    dbc.Col(dbc.Button(
                                [
                                    html.I(className="bi bi-lightning-charge-fill me-2"),
                                    "TRADE"
                                ],
                                id="trade-button",
                                color="info",
                                size="md",
                                className="fw-bold w-100",
                                n_clicks=0,
                                style={
                                    "borderRadius": "12px",
                                    "letterSpacing": "1px",
                                    "background": "linear-gradient(135deg, #2563eb, #1d4ed8)",
                                    "border": "none",
                                    "color": "white",
                                    "boxShadow": "0 6px 16px rgba(37, 99, 235, 0.35)"
                                },
                            )),
                    dbc.Modal([  
                            dbc.ModalBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.H6("Ticker"),
                                    ]),
                                    dbc.Col([
                                        html.Div(
                                            id = "trade-ticker",
                                            className="mb-3",
                                        )
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        html.H6("Type"),
                                    ]),
                                    dbc.Col([
                                        dbc.Select(
                                            id="order-type",
                                            options=[
                                                {"label": "Market Order", "value": "market-order"},
                                                {"label": "Limit Order", "value": "limit-order"},
                                                {"label": "Stop-Loss Order", "value":"stop-loss-order"}
                                            ],
                                            value="market-order",
                                            size="sm",
                                            className="mb-3",

                                        )
                                    ])
                                ]),
                                dbc.Tooltip(
                                    html.Div(
                                        "Market Order: Executed instantly at the best market price available\n" \
                                        "Limit Order: Executed at a specified price or better\n" \
                                        "Stop-Loss order: Trigger a market order at a fixed stop price"
                                        ,
                                        style={"whiteSpace": "pre-line"}
                                    ),
                                    target="order-type",
                                    placement="right",
                                ),
                                dbc.Row([
                                    dbc.Col([
                                        html.H6("Price"),
                                    ]),
                                    dbc.Col([
                                        dbc.InputGroup(
                                            [
                                                dbc.Input(id = "trade-price", value = "", type = "number", step = 0.01, size = "sm", min=0.01),
                                            ],
                                            className="mb-3",
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        html.H6("Quantity"),
                                    ]),
                                    dbc.Col([
                                        dbc.InputGroup(
                                            [
                                                dbc.Input(id = "trade-quantity", value = "1"  , type = "number", size = "sm", min=1),
                                            ],
                                            className="mb-3",
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        html.H6("Amount"),
                                    ]),
                                    dbc.Col([
                                        html.Div(
                                            id = "trade-amount",
                                            className="mb-3",
                                        )
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        html.H6("Time-in-Force"),
                                    ]),
                                    dbc.Col([
                                        dbc.Select(
                                            id="time-in-force",
                                            options=[
                                                {"label": "Day", "value": "day"},
                                                {"label": "Good Till Canceled (GTC)", "value": "gtc"}
                                            ],
                                            value="day",
                                            size="sm" 
                                        )
                                    ])
                                ]),
                                dbc.Tooltip(
                                    html.Div(
                                        "Day: cancels at end of trading day\nGood Till Canceled (GTC): valid up to 90 days",
                                        style={"whiteSpace": "pre-line"}
                                    ),
                                    target="time-in-force",
                                    placement="right",
                                ),
                                html.Br(),
                                html.Hr(),
                                dbc.Row([
                                    dbc.Col(
                                        dbc.Stack([
                                            dbc.Button("Buy", id="buy-button", color="success"),
                                            dbc.Button("Sell", id="sell-button", color="danger"),
                                        ], direction="horizontal", gap = 3),
                                        width="auto"
                                    )
                                ], justify="center"
                                ),
                                html.Br(),
                                dbc.Alert(                                
                                    id="trade-alert",                          
                                    duration=4000,
                                    is_open=False,
                                )               
                            ]
                            )
                        ],
                        id = "trade-modal",
                        is_open = False,
                        scrollable = True,
                        size = "l",
                        fullscreen=False
                        ),
                ], justify = "center"
                ), 

            dbc.Row([
                    dbc.Col([
                        html.Div(
                            id="chat-panel",
                            children=[

                                ############################## HEADER ##############################
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(className="bi bi-chat-dots-fill me-2"),
                                                html.Span("Chat", className="fw-semibold"),
                                            ],
                                            className="d-flex align-items-center",
                                            style={"fontSize": "0.95rem"},
                                        ),

                                        dbc.Button(
                                            html.I(className="bi bi-x-lg"),
                                            id="chat-close",
                                            color="link",
                                            className="ms-auto p-0",
                                        ),
                                    ],
                                    className="d-flex align-items-center bg-body border-bottom",
                                    style={
                                        "padding": "10px 12px",
                                        "borderTopLeftRadius": "16px",
                                        "borderTopRightRadius": "16px",
                                    },
                                ),

                                ############################## CHAT HISTORY ##############################
                                html.Div(
                                    id="chat-history",
                                    className="bg-body",
                                    style={
                                        "height": "300px",
                                        "overflowY": "auto",
                                        "padding": "12px",
                                        "fontSize": "0.9rem",
                                        "lineHeight": "1.35",
                                    },
                                ),

                                ############################## INPUT AREA ##############################
                                html.Div(
                                    [
                                        dbc.InputGroup(
                                            [
                                                dcc.Input(
                                                    id="chat-input",
                                                    type="text",
                                                    placeholder="Type your message...",
                                                    className="form-control",
                                                ),
                                                dbc.Button(
                                                    html.I(className="bi bi-send-fill"),
                                                    id="send-button",
                                                    color="secondary",
                                                    n_clicks=0,
                        ),
                    ]
                )
            ],
            className="bg-body border-top",
            style={
                "padding": "10px 12px",
                "borderBottomLeftRadius": "16px",
                "borderBottomRightRadius": "16px",
            },
        ),

        dcc.Store(id="chat-store", data=[]),
        dcc.Store(id="conversation-store", data=[]),
    ],

    style={
        "display": "none",
        "zIndex": "999",
        "position": "fixed",
        "bottom": "65px",
        "right": "10px",
        "width": "330px",

        "borderRadius": "16px",
        "border": "1px solid var(--bs-border-color)",
        "boxShadow": "0 12px 30px rgba(0,0,0,0.12)",
        "backgroundColor": "var(--bs-body-bg)",
        "overflow": "hidden",
    },
),

                    ], width = "auto",),  
                    dbc.Col(
                        dbc.Button(
                            html.I(
                                className="bi bi-chat-dots-fill",
                                style={"fontSize": "1.5rem", "color": "#0891b2"}  # ⬅ icon size
                            ),
                            id="chat-toggle",
                            outline=True,
                            color="warning",
                            n_clicks=0,
                            style={
                                # positioning (keep yours)
                                "marginTop": "-45px",
                                "marginRight": "45px",

                                # size
                                "width": "48px",
                                "height": "48px",

                                # shape & alignment
                                "borderRadius": "999px",
                                "padding": "0",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",

                                # visuals
                                "backgroundColor": "#ecfeff",
                                "borderColor": "#06b6d4",
                                "boxShadow": "0 8px 20px rgba(0,0,0,0.18)",
                            },
                        ),
                        width="auto",
                        align="end",
                    ),
                    dbc.Modal([ 
                            dbc.ModalHeader("Login", className="fw-bold"), 
                            dbc.ModalBody([
                                dbc.Label("Username"),
                                dbc.Input(id="login-username", type="text", placeholder="Enter username"),
                                html.Br(),
                                dbc.Label("Password"),
                                dbc.Input(id="login-password", type="password", placeholder="Enter password"),
                                html.Br(),
                                dbc.Row(
                                    dbc.Col(
                                        dbc.Button("Login", id="login-submit", color="primary", n_clicks=0, className="mt-2"),
                                        width="auto"
                                    ),
                                    justify="end"
                                ),
                                html.Hr(),
                                dbc.Button("Don't have an account? Click to Register", id = "register-button", color = "link", n_clicks = 0),
                                dbc.Alert(                                
                                    id="login-alert",
                                    duration=4000,
                                    is_open=False,
                                )
                            ]
                            )
                        ],
                        id = "login-modal",
                        is_open = False,
                        scrollable = True,
                        size = "md",
                        ),
                        dbc.Modal([ 
                            dbc.ModalHeader("Register", className="fw-bold"), 
                            dbc.ModalBody([
                                dbc.Label("Username"),
                                dbc.Input(id="register-username", type="text", placeholder="Enter username"),
                                html.Br(),
                                dbc.Label("Password"),
                                dbc.Input(id="register-password", type="password", placeholder="Enter password"),
                                html.Br(),
                                dbc.Row(
                                    dbc.Col(
                                        dbc.Button("Register", id="register-submit", color="primary", n_clicks=0, className="mt-2"),
                                        width="auto"
                                    ),
                                    justify="end"
                                ),
                                html.Hr(),
                                dbc.Button("Already have an account? Log in", id = "login-button", color = "link", n_clicks = 0),
                                dbc.Alert(                                
                                    id="register-alert",                          
                                    duration=4000,
                                    is_open=False,
                                )
                            ]
                            )
                        ],
                        id = "register-modal",
                        is_open = False,
                        scrollable = True,
                        size = "md",
                        )
                ], style={"marginTop": "50px"}, justify = "end"),            
            ], style={"flex": "0 0 350px"})
        ], className="align-items-start"),
        dbc.Toast(
            id="watchlist-toast",
            header="Watchlist",
            is_open=False,
            duration=2000,
            icon="success",
            style={
                "position": "fixed",
                "top": 20,
                "right": 20,
                "zIndex": 9999,
            },
        ),
    ], fluid = True)    
])



##########################################################################################
################################## CALLBACK ##############################################
##########################################################################################

@callback(
    Output("interval", "options"),
    Output("interval", "value"),
    Input("time-period", "value"),
)
def update_interval(time_period):
    if time_period == '1d':
        interval_list = ['1m', '5m', '15m', '30m', '1h']
    elif time_period == '1mo':
        interval_list = ['5m', '15m', '30m', '1h', '1d', '5d', '1wk']
    else:
        interval_list = ['1h', '1d', '5d', '1wk', '1mo', '3mo']
    options = [{'label': i, 'value': i} for i in interval_list]
    value = interval_list[0]

    return options, value



REFRESH_MAP = {
    "1m": 60_000,       # refresh every 1 minute
    "5m": 300_000,      # 5 minutes
    "15m": 900_000,     # 15 minutes
    "1h": 3_600_000,    # 1 hour    
}



@callback(
    Output("live-interval", "interval"),
    Input("live-interval", "n_intervals"),
    Input("interval", "value"),
)
def align_refresh_to_clock(n_intervals, selected_interval):
    # Get base refresh period in ms from the dropdown
    base_ms = REFRESH_MAP.get(selected_interval, 60_000)
    period_sec = base_ms / 1000.0

    # Current time in seconds since epoch
    now = datetime.datetime.now()
    now_ts = now.timestamp()

    # How many seconds until the next multiple of `period_sec`
    # This is: period - (now % period)
    remainder = now_ts % period_sec
    remaining_sec = period_sec - remainder if remainder > 0 else period_sec

    # Small guard against floating point rounding making it ~0
    if remaining_sec < 0.01:
        remaining_sec = period_sec

    return int(remaining_sec * 1000)


@callback(
    Output("price-chart", "figure"),            
    Output("main-metric", "children"),          
    Output("high-metric", "children"),          
    Output("low-metric", "children"),           
    Output("volume-metric", "children"),        
    Output("open-metric", "children"),          
    Output("close-metric", "children"),         
    Output("main-card-container", "style"),     
    Output("watchlist-card-container", "style"),
    Output("main-navbar", "style"),             
    Input("ticker", "value"),
    Input("time-period", "value"),
    Input("interval", "value"),
    Input("chart-type", "value"),
    Input("technical-indicators", "value"),
    Input("live-interval", "n_intervals"),
    Input("theme-toggle", "value")
)
def update_chart(ticker, period, interval, chart_type, indicators, n_intervals, theme):
    
    if not ticker:
        return [no_update] * 10
    
    ticker = ticker.upper()
    data = fetch_stock_data(ticker, period, interval)
    
    if data is None or data.empty:
        empty_fig = go.Figure().update_layout(title=f"No data found for {ticker}")
        return [no_update] * 10

    data = process_data(data)
    data = add_technical_indicators(data)   
    last_close, change, pct_change, high, low, volume, last_open, last_close = calculate_metrics(data)

    # THEME DEFINITIONS
    nav_bg = "#111827" if theme else "#4F46E5"
    card_bg = "#1e1e1e" if theme else "#e3f2fd"
    text_color = "#ffffff" if theme else "#0f172a"
    muted_text = "#a1a1aa" if theme else "#6c757d"

    # DYNAMIC STYLES
    navbar_style = {"backgroundColor": nav_bg, "transition": "0.3s ease"}
    
    container_style = {
        "borderRadius": "16px", 
        "backgroundColor": card_bg, 
        "transition": "0.3s ease", 
        "border": "none"
    }
    
    watchlist_style = {
        "borderRadius": "16px", 
        "backgroundColor": card_bg, 
        "marginBottom": "12px", 
        "marginTop": "20px", 
        "transition": "0.3s ease", 
        "border": "none"
    }

    # CARD CONTENT
    main_card = [
        dbc.Row([
            dbc.Col(html.Div(ticker, className="text-uppercase fw-bold", style={"fontSize": "1rem", "color": muted_text}), width="auto"),
            dbc.Col(dbc.Button(html.I(className="bi bi-plus-lg"), id={"type": "add-watchlist-btn", "ticker": ticker}, color="success", outline=True, size="sm"), width="auto"),
        ], align="center", className="mb-1 d-flex justify-content-between"),
        html.Div(f"{last_close:.2f}", className="fw-bold", style={"fontSize": "2.2rem", "color": text_color}),
        html.Div(f"{change:+.2f} ({pct_change:+.2f}%)", className=("fw-semibold " + ("text-success" if change >= 0 else "text-danger")), style={"fontSize": "0.85rem"}),
    ]

    def get_small_card(label, value, color):
        return [
            html.Div(label, className="text-muted fw-semibold", style={"fontSize": "0.7rem"}),
            html.Div(value, className="fw-bold", style={"fontSize": "0.85rem", "color": color if color else text_color})
        ]

    high_card = get_small_card("HIGH", f"{high:.2f}", "#16a34a")
    low_card = get_small_card("LOW", f"{low:.2f}", "#dc2626")
    vol_card = get_small_card("VOLUME", f"{volume:,}", "#7c3aed")
    open_card = get_small_card("OPEN", f"{last_open:.2f}", "#2563eb")
    close_card = get_small_card("CLOSE", f"{last_close:.2f}", text_color)

    # GRAPH LOGIC
    if 'RSI' in indicators:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.1)
    else:
        fig = make_subplots(rows=1, cols=1)

    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'], open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price"), row=1, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False)
    else:
        fig.add_trace(go.Scatter(x=data['Datetime'], y=data['Close'], name="Price", line=dict(color="#2563eb")), row=1, col=1)

    # Indicator Traces
    if 'SMA 20' in indicators: fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'), row=1, col=1)
    if 'EMA 20' in indicators: fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'), row=1, col=1)
    if 'WMA 20' in indicators: fig.add_trace(go.Scatter(x=data['Datetime'], y=data['WMA_20'], name='WMA 20'), row=1, col=1)
    if 'KAMA' in indicators: fig.add_trace(go.Scatter(x=data['Datetime'], y=data['KAMA'], name='KAMA'), row=1, col=1)

    if 'RSI' in indicators:
        fig.add_trace(go.Scatter(x=data['Datetime'], y=data['RSI'], name="RSI", line=dict(color="purple")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(
        title=f"{ticker.upper()} {period.upper()} Chart",
        template="plotly_dark" if theme else "plotly_white",
        paper_bgcolor="#1e1e1e" if theme else "white",
        plot_bgcolor="#1e1e1e" if theme else "white",
        font=dict(color="white" if theme else "black"),
        margin=dict(t=30, b=30, l=30, r=30)
    )

    return (fig, main_card, high_card, low_card, vol_card, open_card, close_card, 
            container_style, watchlist_style, navbar_style)


@callback(
    Output("watchlist-toast", "is_open", allow_duplicate=True),
    Output("watchlist-toast", "children", allow_duplicate=True),
    Output("watchlist-update-signal", "data", allow_duplicate=True),
    Input({"type": "add-watchlist-btn", "ticker": ALL}, "n_clicks"),
    State("watchlist-update-signal", "data"),
    prevent_initial_call=True
)
def add_to_watchlist(n_clicks, current_signal):
    if not n_clicks or all(click is None or click == 0 for click in n_clicks):
        raise PreventUpdate

    if not current_user.is_authenticated:
        raise PreventUpdate

    triggered = ctx.triggered_id
    ticker = triggered["ticker"]

    exists = Watchlist.query.filter_by(
        user_id=current_user.id,
        ticker=ticker
    ).first()

    if exists:
        return True, f"{ticker} is already in your watchlist", no_update

    db.session.add(Watchlist(user_id=current_user.id, ticker=ticker))
    db.session.commit()

    # Increment signal to trigger load_watchlist
    return True, f"{ticker} added to watchlist ✅", (current_signal or 0) + 1



@callback(
    Output("chat-panel", "style"),
    Input("chat-toggle", "n_clicks"),
    Input("chat-close", "n_clicks"),
    State("chat-panel", "style"),
    prevent_initial_call=True,
)
def toggle_chat(toggle_clicks, close_clicks, style):
    style = (style or {}).copy()

    triggered = ctx.triggered_id
    if triggered is None:
        raise PreventUpdate

    # Close button always hides
    if triggered == "chat-close":
        style["display"] = "none"
        return style

    # Toggle button flips based on click parity
    if triggered == "chat-toggle":
        toggle_clicks = toggle_clicks or 0
        style["display"] = "block" if (toggle_clicks % 2 == 1) else "none"
        return style

    raise PreventUpdate



@callback(
    Output("chat-history", "children"),
    Output("chat-store", "data"),
    Output("conversation-store", "data"),
    Output("chat-input", "value"),
    Input("send-button", "n_clicks"),
    State("chat-input", "value"),
    State("chat-store", "data"),
    State("conversation-store", "data")
)
def send_message(n_clicks, text, chat_history, conversation):
    if not text:
        return no_update, no_update, no_update, no_update
    
    if chat_history is None:
        chat_history = []

    if conversation is None:
        conversation = []
    
    chat_history.append({        
        "role": "user",
        "parts": [{"text": text}]
    })

    sdk_messages = []
    for msg in chat_history:
        sdk_messages.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part(text=p.get("text", "")) for p in msg.get("parts", [])]
            )
        )

    new_message = html.Div([
        html.Strong("You: "),
        html.Span(text)
    ], style={
        "marginBottom": "8px",
        "alignSelf": "flex-end",
        "textAlign": "right",
    },)

    conversation.append(new_message)

    response_text = generate_once(chat_history)

    chat_history.append({       
        "role": "model",
        "parts": [{"text": response_text}]
    })
    
    response_message = html.Div([
        html.Strong("Chatbot: "),
        dcc.Markdown(response_text)
    ], style={
        "marginBottom": "8px",
        "alignSelf": "flex-start",
        "textAlign": "left",
    })


    conversation.append(response_message)

    return conversation, chat_history, conversation, ""



@callback(
    Output("lstm-modal", "is_open"),
    Input("LSTM", "n_clicks"),
    State("lstm-modal", "is_open")
)
def toggle_lstm_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open    
    


@callback(
    Output("lstm-graphs-1", "figure"),
    Output("lstm-graphs-2", "figure"),
    Output("lstm-graphs-3", "figure"),
    Output("lstm-graphs-4", "figure"),
    Output("lstm-cache", "data"),
    Input("LSTM", "n_clicks"),
    State("ticker", "value"),
    State("lstm-cache", "data"),    
)
def lstm_graphs(n_clicks, ticker, cache):
    if not n_clicks:
        raise PreventUpdate
    
    ticker = ticker.upper()
    cache = cache or {}

    if ticker in cache:
        result = cache[ticker]
    else:
        data = yf.download(ticker, start='2010-01-01', end=datetime.datetime.today().strftime('%Y-%m-%d'))
        data = data[['Close']]

        (train_predictions, y_train,
            val_predictions, y_val,
            test_predictions, y_test,
            past_30_dates, past_prices,
            next_day_date, next_day_price) = lstm_model(data)
        
        #y_past = np.asarray(past_prices, dtype=float).reshape(-1)   # (30,)
        #y_pred = float(np.asarray(next_day_price).reshape(())) 

        result = {
            "train_predictions": list(map(float, np.asarray(train_predictions).reshape(-1))),
            "y_train":           list(map(float, np.asarray(y_train).reshape(-1))),
            "val_predictions":   list(map(float, np.asarray(val_predictions).reshape(-1))),
            "y_val":             list(map(float, np.asarray(y_val).reshape(-1))),
            "test_predictions":  list(map(float, np.asarray(test_predictions).reshape(-1))),
            "y_test":            list(map(float, np.asarray(y_test).reshape(-1))),
            "past_30_dates":     [str(pd.to_datetime(d)) for d in pd.to_datetime(past_30_dates)],
            "y_past":            list(map(float, np.asarray(past_prices).reshape(-1))),
            "next_day_date":     str(pd.to_datetime(next_day_date)),
            "y_pred":            float(np.asarray(next_day_price).reshape(())),
        }
        
        
        cache[ticker] = result
    
    #fig = make_subplots(rows = 4, cols = 1, subplot_titles=("Prediction", "Test_Set", "Validation_Set", "Training_Set"))

    fig1 = go.Figure()
    fig2 = go.Figure()
    fig3 = go.Figure()
    fig4 = go.Figure()

    # Training Set
    fig1.add_trace(go.Scatter(y = result["train_predictions"], mode="lines", name="train_predictions"))
    fig1.add_trace(go.Scatter(y = result["y_train"],           mode="lines", name="y_train"))

    # Validation Set
    fig2.add_trace(go.Scatter(y = result["val_predictions"], mode="lines", name="val_predictions"))
    fig2.add_trace(go.Scatter(y = result["y_val"],           mode="lines", name="y_val"))

    # Test Set
    fig3.add_trace(go.Scatter(y = result["test_predictions"], mode="lines", name="test_predictions"))
    fig3.add_trace(go.Scatter(y = result["y_test"],           mode="lines", name="y_test"))
    
    # Prediction
    fig4.add_trace(go.Scatter(x = pd.to_datetime(result["past_30_dates"]), y = result["y_past"], mode="lines", name="Past 30 Days"))
    fig4.add_trace(go.Scatter(x = [pd.to_datetime(result["next_day_date"])], y = [result["y_pred"]], mode="markers", name="Predicted Next Day"))
    
    # Update layout
    fig4.update_xaxes(title_text="Date",)
    fig4.update_yaxes(title_text="Price")

    #fig.update_layout(title_text="LSTM Results")

    return fig4, fig3, fig2, fig1, cache



@callback(
    Output("xgboost-modal", "is_open"),
    Input("XGBoost", "n_clicks"),
    State("xgboost-modal", "is_open")
)
def toggle_xgboost_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open  



@callback(
    Output("xgboost-results-text", "children"),
    Output("xgboost-graph", "figure"),
    Output("xgboost-cache", "data"),
    Input("xgboost-modal", "is_open"),
    State("ticker", "value"),
    State("xgboost-cache", "data"),    
    prevent_initial_call=True
)
def xgboost_graph(is_open, ticker, cache):
    if not is_open or not ticker:
        raise PreventUpdate
    
    ticker = ticker.upper()
    cache = cache or {}

    if ticker in cache:
        result = cache[ticker]
        dates, target, pred, rmse, mape = result["index"], result["target"], result["pred"], result["rmse"], result["mape"]
    else:
        data = yf.download(ticker, start="2010-01-01", end=datetime.datetime.today().strftime('%Y-%m-%d'))
        data_TP, model_rmse, model_mape = xgboost_model(data)
        dates = data_TP.index.astype(str).tolist()
        target = data_TP["Target"].astype(float).tolist()
        pred = data_TP["Pred"].astype(float).tolist()
        result = {"index": dates, "target": target, "pred": pred, "rmse": float(model_rmse), "mape": float(model_mape)}
        cache[ticker] = result
        rmse, mape = result["rmse"], result["mape"]

    latest_actual = target[-1]
    latest_pred = pred[-1]
    direction_up = latest_pred > latest_actual
    direction_text = "UP 📈" if direction_up else "DOWN 📉"
    
    results_text = html.Div([
        html.H4(f"{ticker} — XGBoost Result", className="fw-bold mb-1"),
        html.P(f"RMSE: {rmse:.2f} | MAPE: {mape:.2f}%", className="mb-1", style={"fontSize": "14px"}),
        html.P([
            "Prediction: ", 
            html.B(direction_text)
        ], className="mb-1", style={"fontSize": "14px"}),
        html.P(f"Predicted Price: ${latest_pred:.2f}", style={"fontSize": "14px"}),
        html.Hr(className="my-3")
    ], className="text-center mt-2")

    fig = go.Figure()

    # Actual Price - Blue
    fig.add_trace(go.Scatter(
        x=dates, 
        y=target, 
        name="Actual Price", 
        line=dict(color="#0ea5e9", width=2)
    ))

    # Predicted Price - Orange (Solid line, no dash)
    fig.add_trace(go.Scatter(
        x=dates, 
        y=pred, 
        name="Predicted Price", 
        line=dict(color="#f59e0b", width=2)
    ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        height=600,
        template="plotly_white", 
        margin=dict(t=10, b=50, l=50, r=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return results_text, fig, cache



@callback(
    Output("svm-modal", "is_open"),
    Input("SVM", "n_clicks"),
    State("svm-modal", "is_open")
)
def toggle_svm_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open



@callback(
    Output("svm-graph", "figure"),
    Output("svm-cache", "data"),
    Input("svm-modal", "is_open"),  # Trigger whenever the modal opens or closes
    State("ticker", "value"),
    State("svm-cache", "data"),
    prevent_initial_call=True
)
def svm_graph(is_open, ticker, cache):
    # Only proceed if the modal is actually opening
    if not is_open or not ticker:
        raise PreventUpdate
    
    ticker = ticker.upper()
    cache = cache or {}

    # Step 1: Check Cache
    if ticker in cache:
        result = cache[ticker]
        train_accuracy = result["train_accuracy"]
        test_accuracy = result["test_accuracy"]
        tomorrow_signal = result["tomorrow_signal"]
        prob_up = result["prob_up"]
        prob_down = result["prob_down"]
        
        # Load DataFrame from cached dictionary
        df = pd.DataFrame(result["data"])
        
        # Restore the index 
        if 'Datetime' in df.columns:
            df.index = pd.to_datetime(df['Datetime'])
        elif 'index' in df.columns:
            df.index = pd.to_datetime(df['index'])
    
    # Step 2: Run Model if not in Cache
    else:
        data = yf.download(
            ticker,
            start="2010-01-01",
            end=datetime.datetime.today().strftime('%Y-%m-%d')
        )
        # Run existing svm_model function
        train_accuracy, test_accuracy, tomorrow_signal, prob_up, prob_down, df = svm_model(data)

        # Store results in cache dictionary
        result = {
            "train_accuracy": train_accuracy,
            "test_accuracy": test_accuracy,
            "tomorrow_signal": int(tomorrow_signal),
            "prob_up": float(prob_up),
            "prob_down": float(prob_down),
            "data": df.reset_index().to_dict(orient="records"), # .reset_index() ensures the Date/Datetime index is saved as a column
        }
        cache[ticker] = result

    # Step 3: Generate the Figure
    # This part now runs regardless of whether the data was new or cached
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=df['Cum_Ret'],
        mode='lines', name='Buy & Hold', line=dict(color='red')
    ))

    fig.add_trace(go.Scatter(
        x=df.index, y=df['Cum_Strategy'],
        mode='lines', name='SVM Strategy', line=dict(color='blue')
    ))

    direction_text = "UP 📈" if tomorrow_signal == 1 else "DOWN 📉"

    fig.update_layout(
        title=(
            f"<b>{ticker} — SVM Result</b><br>"
            f"<span style='font-size: 14px;'>Train Acc: {train_accuracy*100:.2f}% | "
            f"Test Acc: {test_accuracy*100:.2f}%</span><br>"
            f"<span style='font-size: 14px;'>Prediction: <b>{direction_text}</b></span><br>"
            f"<span style='font-size: 14px;'>UP Probability: {prob_up:.2f}% | DOWN Probability: {prob_down:.2f}%</span>"
        ),
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        height=700,
        margin=dict(t=120, b=50, l=50, r=50),
        title_x=0.5,
        title_y=0.95,
        template="plotly_white"
    )

    return fig, cache



@callback(
    Output("rf-modal", "is_open"),
    Input("randomforest", "n_clicks"),
    State("rf-modal", "is_open")
)
def toggle_rf_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open



@callback(
    Output("rf-results", "children"),
    Output("rf-cache", "data"),
    Input("randomforest", "n_clicks"),
    State("ticker", "value"),
    State("rf-cache", "data"),    
)
def rf_results(n_clicks, ticker, cache):
    if not n_clicks:
        raise PreventUpdate
    
    ticker = (ticker or "").upper()
    cache = cache or {}

    # Use cache if available 
    if ticker in cache:
        result = cache[ticker]
        precision = result["precision"]
        next_day_direction = result["next_day_direction"]

    else:
        # Download data and run model
        data = yf.download(
            ticker,
            start="2010-01-01",
            end=datetime.datetime.today().strftime('%Y-%m-%d')
        )

        if data.empty:
            return html.Div(f"No data available for {ticker}"), cache

        precision, next_day_direction, df = rf_model(data)

        # Make JSON-safe cache entry
        result = {
            "precision": float(precision),
            "next_day_direction": int(next_day_direction),
            "data": df.reset_index().rename(columns={"index": "Date"}).to_dict(orient="records"),
        }
        cache[ticker] = result

    # Build text output (no graph) 
    direction_text = "UP 📈" if next_day_direction == 1 else "DOWN 📉"

    children = [
        html.H5(f"{ticker} — Random Forest Result"),
        html.P(f"Precision on test set: {precision*100:.2f}%"),
        html.P(f"Predicted direction for next day: {direction_text}"),
    ]

    return children, cache




@callback(
    Output("trade-modal", "is_open"),
    Input("trade-button", "n_clicks"),
    State("trade-modal", "is_open")
)
def toggle_trade_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open      



@callback(
    Output("trade-ticker", "children"),
    Input("ticker", "value")
)
def trade_ticker(ticker):
    ticker = ticker.upper()
    return ticker



@callback(
    Output("trade-price", "value"),
    Input("ticker", "value"),
    Input("time-period", "value"),
    Input("interval", "value")
)
def trade_price(ticker, period, interval):
    if not ticker:
        return no_update
    
    ticker = ticker.upper()
    
    # Fetch the data 
    data = fetch_stock_data(ticker, period, interval)
    
    # Handle cases where yfinance returns None or is empty
    if data is None or data.empty:
        return no_update
    
    # Clean the data 
    data = process_data(data)
    
    close_data = data['Close']
    
    if isinstance(close_data, pd.DataFrame):
        # If multiple 'Close' columns exist, take the first one (iloc index 0)
        last_val = close_data.iloc[-1, 0]
    else:
        # Standard Series behavior
        last_val = close_data.iloc[-1]
    
    if hasattr(last_val, '__len__') and not isinstance(last_val, (str, bytes)):
        last_val = last_val[0]
        
    try:
        return float(f"{last_val:.2f}")
    except (TypeError, ValueError):
        return no_update



@callback(
    Output("trade-amount", "children"),
    Input("trade-price", "value"),
    Input("trade-quantity", "value")
)   
def trade_amount(price, quantity):

    if not price or not quantity:
        return no_update

    amount = price * float(quantity)
    return amount   



@callback(
    Output("login-modal", "is_open", allow_duplicate=True),
    Output("trade-modal", "is_open", allow_duplicate=True),
    Output("trade-alert", "children"),
    Output("trade-alert", "color"),
    Output("trade-alert", "is_open"),
    Input("buy-button", "n_clicks"),
    Input("sell-button", "n_clicks"),
    State("ticker", "value"),
    State("trade-price", "value"),
    State("trade-quantity", "value"),
    prevent_initial_call=True
)
def trade_or_login(n_buy, n_sell, ticker, price, quantity):
    
    if not ctx.triggered_id:
        raise PreventUpdate
    side = ctx.triggered_id  # buy-button or sell-button

    # If not logged in -> open login modal, close trade modal closed
    if not getattr(current_user, "is_authenticated", False):
        return True, False, no_update, no_update, no_update
    
    ticker = ticker.upper()
    price = float(price)
    quantity = float(quantity)
    
    if price <= 0 or quantity <= 0:
        return False, no_update, "Price and quantity must be positive.", "warning", True

    # Load user fresh
    user = User.query.get(current_user.id)
    if user is None:
        return False, no_update, "User not found.", "danger", True

    try:
        if side == "buy-button":
            cost = price * quantity
            if cost > user.balance:
                return False, no_update, "Insufficient balance.", "warning", True

            holding = StockHolding.query.filter_by(user_id=user.id, ticker=ticker).first()
            if holding:
                total_cost = holding.shares * holding.avg_price + cost
                holding.shares += quantity
                holding.avg_price = total_cost / holding.shares
                holding.total_value = holding.shares * holding.avg_price
            else:
                db.session.add(StockHolding(
                    user_id=user.id,
                    ticker=ticker,
                    shares=quantity,
                    avg_price=price,
                    total_value=quantity * price 
                ))

            user.balance -= cost
            db.session.commit()
            return False, no_update, f"Bought {quantity:g} {ticker} @ ${price:,.2f}.", "success", True

        elif side == "sell-button":
            holding = StockHolding.query.filter_by(user_id=user.id, ticker=ticker).first()
            if holding is None or holding.shares < quantity:
                return False, no_update, "Not enough shares to sell.", "warning", True

            proceeds = price * quantity
            holding.shares -= quantity
            if holding.shares <= 0:
                db.session.delete(holding)
            else:
                holding.total_value = holding.shares * holding.avg_price     
                
            user.balance += proceeds
            db.session.commit()
            return False, no_update, f"Sold {quantity:g} {ticker} @ ${price:,.2f}.", "success", True

        else:
            return False, no_update, "Unknown action.", "danger", True

    except Exception as e:
        db.session.rollback()
        return False, no_update, f"Trade failed: {e}", "danger", True



@callback(
    Output("login-modal", "is_open", allow_duplicate=True),
    Input("register-button", "n_clicks"),
    Input("login-button", "n_clicks"),
    State("login-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_login(n2, n3, is_open):
    if n2 or n3:
        return not is_open
    return is_open



@callback(
    Output("register-modal", "is_open"),
    Input("login-button", "n_clicks"),
    Input("register-button", "n_clicks"),
    State("register-modal", "is_open")
)
def toggle_register(n2, n1, is_open):
    if n2 or n1:
        return not is_open
    return is_open



@callback(
    Output("login-modal", "is_open", allow_duplicate=True),
    Output("router", "href", allow_duplicate=True),
    Input("login-toggle", "n_clicks"),
    State("login-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_account_page(n_clicks, is_open):
    if not n_clicks:
        raise PreventUpdate
    if getattr(current_user, "is_authenticated", False):
        return is_open, "/account"
    return not is_open, no_update



@callback(
    Output("login-text", "children"),
    Input("login-toggle", "n_clicks"),
    prevent_initial_call=False
)
def update_nav_label(_):
    if current_user.is_authenticated:
        return "Profile"
    return "Login"



@callback(
    Output("nav-collapse", "is_open"),
    Input("nav-toggler", "n_clicks"),
    State("nav-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_nav(n, is_open):
    if not n:
        raise PreventUpdate
    return not is_open



@callback(
    Output("register-alert", "children"),
    Output("register-alert", "color"),
    Output("register-alert", "is_open"),
    Output("register-username", "value"),
    Output("register-password", "value"),
    Input("register-submit", "n_clicks"),
    State("register-username", "value"),
    State("register-password", "value"),
    prevent_initial_call=True
)
def registration(n_clicks, username, password):
    if not username or not password:
        return "All fields are required!", "danger", True, no_update, no_update
    if len(username) < 5:
        return "Username must be at least 8 characters long.", "danger", True, no_update, no_update
    if len(password) < 8:
        return "Username must be at least 8 characters long.", "danger", True, no_update, no_update
    
    existing_user_name = User.query.filter_by(username = username).first()

    if existing_user_name:
        return "Username already exists. Please choose a different one", "danger", True, no_update, no_update
    
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    return "Registration successful!", "success", True, "", ""



@callback(
    Output("login-alert", "children"),
    Output("login-alert", "color"),
    Output("login-alert", "is_open"),
    Output("login-username", "value"),
    Output("login-password", "value"),
    Output("router", "href"),
    Input("login-submit", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def login(n_clicks, username, password):
    if not username or not password:
        return "All fields are required!", "danger", True, no_update, no_update, no_update
    if len(username) < 5:
        return "Username must be at least 8 characters long.", "danger", True, no_update, no_update, no_update

    user = User.query.filter_by(username=username).first()
    if not user:
        return "Invalid username or password.", "danger", True, no_update, no_update, no_update

    if not bcrypt.check_password_hash(user.password, password):
        return "Invalid username or password.", "danger", True, no_update, no_update, no_update

    login_user(user)
    return "Login successful!", "success", True, "", "", "/account"



@callback(
    Output("theme-link", "href"),
    Output("theme-store", "data"),
    Input("theme-toggle", "value"),
)
def switch_theme(is_dark):
    theme_url = dbc.themes.DARKLY if is_dark else dbc.themes.BOOTSTRAP
    return theme_url, theme_url


@callback(
    Output("trade-price", "value", allow_duplicate=True),
    Output("trade-price", "disabled", allow_duplicate=True),
    Input("order-type", "value"),
    Input("trade-modal", "is_open"),
    State("trade-price", "value"),
    prevent_initial_call=True
)
def handle_market_price(order_type, is_open, current_price):
    if not is_open:
        raise PreventUpdate

    # Market Order 
    if order_type == "market-order":
        return current_price, True   # keep latest price, disable input

    # Limit / Stop-Loss
    return no_update, False          



@callback(
    Output("watchlist-items", "children"),
    Input("watchlist-update-signal", "data"), # Primary Trigger: Wait for the signal change
    Input("router", "pathname"),             # Trigger on page load
    Input("live-interval", "n_intervals"),   # Trigger on periodic refresh
    State("theme-toggle", "value"),          # State: just check the value, don't trigger
)
def load_watchlist(signal, pathname, n_intervals, theme):
    # This logic runs immediately every time 'signal' is incremented
    if not current_user.is_authenticated:
        return html.Div("Log in to use watchlist", className="text-muted small p-2")

    # Define theme colors
    text_color = "white" if theme else "#0f172a"
    item_bg = "#2d2d2d" if theme else "#ffffff"

    # Fetch fresh list from DB 
    watchlist_entries = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.ticker).all()

    if not watchlist_entries:
        return html.Div("No stocks in watchlist", className="text-muted small p-2")

    watchlist_cards = []
    
    for entry in watchlist_entries:
        symbol = entry.ticker
        try:
            real_time_data = fetch_stock_data(symbol, '1d', '1m')
            real_time_data = process_data(real_time_data)
            
            last_price = real_time_data['Close'].iloc[-1]
            change = last_price - real_time_data['Open'].iloc[-1]
            pct_change = (change / real_time_data['Open'].iloc[-1]) * 100

            card = dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(html.H6(symbol, className="mb-0 fw-bold", style={"color": text_color}), width=5),
                        dbc.Col(
                            html.P(f"{pct_change:+.2f}%",
                                   className=f"small mb-0 text-end {'text-success' if change >= 0 else 'text-danger'}"), 
                            width=4
                        ),
                        dbc.Col(
                            dbc.Button(
                                html.I(className="bi bi-x"),
                                id={"type": "delete-watchlist-btn", "ticker": symbol},
                                size="md",
                                color="link",
                                className="p-0 text-danger",
                                style={"textDecoration": "none", "fontSize": "1.8rem", "fontWeight": "bold", "lineHeight": "1", "marginTop": "-5px"}
                            ),
                            width=3,
                            className="text-end"
                        )
                    ]),
                    html.H5(f"${last_price:,.2f}", className="mt-1 mb-0", style={"color": text_color}),
                ], className="p-2"),
                className="mb-2 shadow-sm border-0",
                style={"borderRadius": "12px", "backgroundColor": item_bg}
            )
            watchlist_cards.append(card)
        except Exception as e:
            continue

    return watchlist_cards

@callback(
    Output("watchlist-toast", "is_open", allow_duplicate=True),
    Output("watchlist-toast", "children", allow_duplicate=True),
    Output("watchlist-update-signal", "data", allow_duplicate=True),
    Input({"type": "delete-watchlist-btn", "ticker": ALL}, "n_clicks"),
    State("watchlist-update-signal", "data"),
    prevent_initial_call=True
)
def delete_from_watchlist(n_clicks, current_signal):
    if not n_clicks or not any(n_clicks):
        raise PreventUpdate

    triggered_id = ctx.triggered_id
    ticker_to_delete = triggered_id["ticker"]

    entry = Watchlist.query.filter_by(
        user_id=current_user.id, 
        ticker=ticker_to_delete
    ).first()

    if entry:
        db.session.delete(entry)
        db.session.commit()
        # Increment signal to trigger load_watchlist
        return True, f"Removed {ticker_to_delete} from watchlist.", (current_signal or 0) + 1
    
    return no_update, no_update, no_update