from dash import html, dcc, register_page, callback, Output, Input, State, no_update, ctx, ALL
from flask_login import current_user, logout_user
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from extensions import db, User, StockHolding
import yfinance as yf
import time

register_page(__name__, path="/account")

layout = dbc.Container([
    dcc.Location(id="account-router"),
    dcc.Store(id="account-refresh", data=0),

    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.Div(
                        [
                            html.I(className="bi bi-person-circle fs-1 text-primary"),
                            html.Div(id="acc-username", className="fw-semibold fs-5 mt-2"),
                            html.Small("Account Overview", className="text-muted"),
                        ],
                        className="text-center mb-3"
                    ),

                    html.Hr(),

                    dbc.Nav(
                        [
                            dbc.NavLink(
                                [html.I(className="bi bi-house me-2"), "Home"],
                                href="/",
                                active="exact"
                            ),
                            dbc.NavLink(
                                [html.I(className="bi bi-arrow-left-right me-2"), "Transfer"],
                                id="nav-transfer",
                                style={"cursor": "pointer"}
                            ),
                            dbc.NavLink(
                                [html.I(className="bi bi-box-arrow-right me-2"), "Logout"],
                                id="nav-logout",
                                className="text-danger",
                                style={"cursor": "pointer"}
                            ),
                        ],
                        vertical=True,
                        pills=True
                    ),

                    # keep logout modal here
                    dbc.Modal(
                        [
                            dbc.ModalBody("Are you sure you want to log out?"),
                            dbc.ModalFooter([
                                dbc.Button("Cancel", id="logout-cancel", className="me-2"),
                                dbc.Button("Confirm", id="logout-confirm", color="danger"),
                            ]),
                        ],
                        id="logout-modal",
                        is_open=False,
                        backdrop="static",
                        centered=True,
                    ),
                ]),
                className="shadow-sm h-100"
            ),
            width=2
        ),
       
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.Div("Total Assets", className="text-muted"),
                                    html.H3(id="account-assets", className="fw-bold"),
                                    html.I(className="bi bi-wallet2 fs-3 text-primary"),
                                ],
                                className="d-flex justify-content-between align-items-center"),
                                className="shadow-sm"
                            ),
                            width=6
                        ),

                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.Div("Available Balance", className="text-muted"),
                                    html.H3(id="account-balance", className="fw-bold"),
                                    html.I(className="bi bi-cash-stack fs-3 text-success"),
                                ],
                                className="d-flex justify-content-between align-items-center"),
                                className="shadow-sm"
                            ),
                            width=6
                        ),
                    ]),

                    html.Hr(),

                    dbc.Alert(
                        [
                            html.Span("Total P/L: "),
                            html.Strong(id="account-pnl"),
                        ],
                        className="text-center fw-semibold",
                        color="light"
                    ),

                    html.Hr(),

                    html.Div("Positions", className="fw-semibold fs-4 mb-2"),
                    html.Div(id="positions-table"),
                ]),
                className="shadow-sm"
            ),
            width=6
        ),

        dbc.Modal([
            dbc.ModalHeader([
                html.I(className="bi bi-arrow-left-right me-2"),
                "Transfer Funds"
                ], 
                className = "fw-bold"),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Type"),
                    ]),
                    dbc.Col([
                        dbc.Select(
                            id="transfer-type",
                            options=[
                                {"label": "Deposit", "value": "deposit"},
                                {"label": "Withdraw", "value": "withdraw"},
                            ],
                            value="deposit",
                            size="sm",
                            className="mb-3",

                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6("Amount"),
                    ]),
                    dbc.Col([
                        dbc.Input(id = "transfer-amount", value = "0.01", type = "number", step = 0.01, size = "sm", min=0.01, className = "mb-3"),
                    ])
                ]),
                dbc.Alert(id="transfer-alert", is_open=False, duration=3000)
            ]),
            dbc.ModalFooter(
                dbc.Button("Confirm", id="confirm-transfer", color="primary", size="lg", className="w-100")
            ),
        ],
        id = "transfer-modal",
        is_open = False,
        size = "l",
        centered = True
        ),

        dbc.Modal([  
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Ticker"),
                    ]),
                    dbc.Col([
                        html.Div(
                            id = "trade-ticker-2",
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
                            id="order-type-2",
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
                    target="order-type-2",
                    placement="right",
                ),
                dbc.Row([
                    dbc.Col([
                        html.H6("Price"),
                    ]),
                    dbc.Col([
                        dbc.InputGroup(
                            [
                                dbc.Input(id = "trade-price-2", value = "", type = "number", step = 0.01, size = "sm", min=0.01),
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
                                dbc.Input(id = "trade-quantity-2", value = "1"  , type = "number", size = "sm", min=1),
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
                            id = "trade-amount-2",
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
                            id="time-in-force-2",
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
                    target="time-in-force-2",
                    placement="right",
                ),
                html.Br(),
                html.Hr(),
                dbc.Row([
                    dbc.Col(
                        dbc.Stack([
                            dbc.Button("Buy", id="buy-button-2", color="success"),
                            dbc.Button("Sell", id="sell-button-2", color="danger"),
                        ], direction="horizontal", gap = 3),
                        width="auto"
                    )
                ], justify="center"
                ),
                html.Br(),
                dbc.Alert(                                
                    id="trade-alert-2",                          
                    duration=4000,
                    is_open=False,
                )               
            ]
            )
        ],
        id = "trade-modal-2",
        is_open = False,
        scrollable = True,
        size = "l",
        fullscreen=False
        ),

    ], className="mt-4 justify-content-center"),
], fluid=True)



@callback(
    Output("acc-username", "children"),
    Input("account-router", "pathname"),
    prevent_initial_call=False
)
def show_username(pathname):
    return current_user.username if getattr(current_user, "is_authenticated", False) else "Guest"



@callback(
    Output("account-balance", "children"),
    Input("account-router", "pathname"),
    Input("account-refresh", "data"),
    prevent_initial_call=False
)
def show_balance(_, __):
    if not getattr(current_user, "is_authenticated", False):
        return "$0.00"

    user = User.query.get(current_user.id)
    return f"${float(user.balance):,.2f}"



@callback(
    Output("account-assets", "children"),
    Input("account-router", "pathname"),
    Input("account-refresh", "data"),
    prevent_initial_call=False
)
def show_assets(_, __):
    # Not logged in
    if not getattr(current_user, "is_authenticated", False):
        return "$0.00"

    # Load user from DB
    user = User.query.get(current_user.id)
    if user is None:
        return "$0.00"

    cash = float(user.balance)

    # Fetch all holdings
    positions = StockHolding.query.filter_by(user_id=current_user.id).all()
    if not positions:
        return f"${cash:,.2f}"

    # ----- Fetch current prices using the same method as your positions table -----
    tickers = sorted({p.ticker for p in positions})
    price_map = {}

    for t in tickers:
        try:
            data = yf.Ticker(t).history(period="1d")
            if not data.empty:
                price_map[t] = float(data["Close"].iloc[-1])
            else:
                price_map[t] = None
        except Exception:
            price_map[t] = None

    # ----- Calculate total asset value -----
    total_market_value = 0.0
    for p in positions:
        current_price = price_map.get(p.ticker)

        if current_price is not None:
            total_market_value += p.shares * current_price

    total_assets = cash + total_market_value

    return f"${total_assets:,.2f}"



@callback(
    Output("logout-modal", "is_open"),
    Output("account-router", "href"),
    Input("nav-logout", "n_clicks"),
    Input("logout-cancel", "n_clicks"),
    Input("logout-confirm", "n_clicks"),
    State("logout-modal", "is_open"),
    prevent_initial_call=True
)
def handle_logout(n_logout, n_cancel, n_confirm, is_open):
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered_id

    if trigger == "nav-logout":
        return True, no_update

    if trigger == "logout-cancel":
        return False, no_update

    if trigger == "logout-confirm":
        logout_user()
        return False, "/"

    return is_open, no_update



@callback(
    Output("transfer-modal", "is_open"),
    Input("nav-transfer", "n_clicks"),
    State("transfer-modal", "is_open")
)
def toggle_transfer_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open 



@callback(
    Output("account-balance", "children", allow_duplicate=True),
    Output("account-assets", "children", allow_duplicate=True),
    Output("transfer-amount", "value"),
    Output("transfer-type", "value"),
    Output("transfer-alert", "children"),
    Output("transfer-alert", "color"),
    Output("transfer-alert", "is_open"),
    Input("confirm-transfer", "n_clicks"),
    State("transfer-type", "value"),
    State("transfer-amount", "value"),
    prevent_initial_call=True
)
def handle_transfer(n_clicks, transfer_type, amount):
    if not n_clicks:
        raise PreventUpdate

    # Must be logged in
    if not getattr(current_user, "is_authenticated", False):
        return (no_update, no_update, no_update,
                "Please log in first.", "danger", True)

    amount = float(amount)
    
    # Load user row fresh from DB
    user = User.query.get(current_user.id)
    if user is None:
        return (no_update, no_update, no_update,
                "User not found.", "danger", True)

    current = float(user.balance)

    if transfer_type == "deposit":
        user.balance = current + amount
    elif transfer_type == "withdraw":
        if amount > current:
            return (no_update, no_update, no_update,
                    "Insufficient funds.", "warning", True)
        user.balance = current - amount
    else:
        return (no_update, no_update, no_update,
                "Unknown transfer type.", "danger", True)

    # Commit to DB
    db.session.commit()

    # Updated balance string
    bal_str = f"${user.balance:,.2f}"

    positions = StockHolding.query.filter_by(user_id=user.id).all()
    total_market_value = sum(p.shares * p.avg_price for p in positions)
    total_assets = user.balance + total_market_value
    assets_str = f"${total_assets:,.2f}"

    success_msg = "Deposit successful!" if transfer_type == "deposit" else "Withdrawal successful!"

    return (
        bal_str,          
        assets_str,       
        "0.01",           
        "deposit",        
        success_msg,      
        "success",        
        True              
    )



@callback(
    Output("positions-table", "children"),
    Output("account-pnl", "children"),
    Input("account-router", "pathname"),
    Input("account-refresh", "data"),
    prevent_initial_call=False
)
def show_positions(_, __):

    # ------------------ Not logged in ------------------
    if not getattr(current_user, "is_authenticated", False):
        return (
            html.Div("Please log in to view your positions.", className="text-muted"),
            html.Span("$0.00", className="text-muted")
        )

    # ------------------ Fetch positions ------------------
    positions = StockHolding.query.filter_by(user_id=current_user.id).all()

    # ------------------ No positions ------------------
    if not positions:
        return (
            html.Div("You currently do not hold any positions.", className="text-muted"),
            html.Span("$0.00", className="text-muted")
        )

    # ------------------ Fetch current prices ------------------
    tickers = sorted({p.ticker for p in positions})
    price_map = {}

    for t in tickers:
        try:
            data = yf.Ticker(t).history(period="1d")
            price_map[t] = float(data["Close"].iloc[-1]) if not data.empty else None
        except Exception:
            price_map[t] = None

    # ------------------ Build table ------------------
    header = html.Thead(
        html.Tr([
            html.Th("Ticker"),
            html.Th("Shares", className="text-end"),
            html.Th("Avg. Price", className="text-end"),
            html.Th("Total Value", className="text-end"),
            html.Th("Current Price", className="text-end"),
            html.Th("P/L", className="text-end"),
            html.Th("Action", className="text-center"),
        ])
    )

    rows = []
    total_pnl = 0.0

    for p in positions:
        current_price = price_map.get(p.ticker) or 0.0
        pnl = (current_price - p.avg_price) * p.shares
        total_pnl += pnl

        rows.append(
            html.Tr([
                html.Td(dbc.Badge(p.ticker, color="secondary", pill=True)),
                html.Td(f"{p.shares:,.2f}", className="text-end"),
                html.Td(f"${p.avg_price:,.2f}", className="text-end"),
                html.Td(f"${p.shares * p.avg_price:,.2f}", className="text-end"),
                html.Td(f"${current_price:,.2f}", className="text-end"),
                html.Td(
                    html.Span(
                        f"${pnl:,.2f}",
                        className="text-success" if pnl >= 0 else "text-danger"
                    ),
                    className="text-end"
                ),
                html.Td(
                    dbc.Button(
                        "Trade",
                        color="info",
                        size="sm",
                        id={"type": "trade-button-2", "ticker": p.ticker}
                    ),
                    className="text-center"
                ),
            ])
        )

    table = dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        striped=True,
        hover=True,
        size="sm",
        responsive=True,
        className="align-middle"
    )

    pnl_display = html.Span(
        f"${total_pnl:,.2f}",
        className="text-success" if total_pnl >= 0 else "text-danger"
    )

    return table, pnl_display



@callback(
    Output("trade-modal-2", "is_open", allow_duplicate=True),
    Output("trade-ticker-2", "children", allow_duplicate=True),
    Output("trade-price-2", "value", allow_duplicate=True),
    Output("trade-alert-2", "children", allow_duplicate=True),
    Output("trade-alert-2", "color", allow_duplicate=True),
    Output("trade-alert-2", "is_open", allow_duplicate=True),
    Output("account-refresh", "data", allow_duplicate=True),  # ✅ ADD THIS

    Input({"type": "trade-button-2", "ticker": ALL}, "n_clicks"),
    Input("buy-button-2", "n_clicks"),
    Input("sell-button-2", "n_clicks"),

    State("trade-modal-2", "is_open"),
    State("trade-ticker-2", "children"),
    State("trade-price-2", "value"),
    State("trade-quantity-2", "value"),

    prevent_initial_call=True
)
def handle_trade(trade_buttons, n_buy, n_sell, is_open, current_ticker, price, quantity):
    trigger = ctx.triggered_id

    # ------------------ No trigger ------------------
    if trigger is None:
        raise PreventUpdate

    # ------------------ Open trade modal ------------------
    if isinstance(trigger, dict) and trigger.get("type") == "trade-button-2":
    # get index in the ALL list
        try:
            idx = trade_buttons.index(ctx.triggered[0]["value"])
        except ValueError:
            raise PreventUpdate

        # only open if button has actually been clicked
        if not trade_buttons[idx]:
            raise PreventUpdate

        ticker = trigger["ticker"]

        # Fetch latest price
        try:
            data = yf.Ticker(ticker).history(period="1d")
            latest_price = round(float(data["Close"].iloc[-1]), 2) if not data.empty else None
        except Exception:
            latest_price = None

        return True, ticker, latest_price, "", "", False, no_update
    

    # ------------------ Buy / Sell ------------------
    if trigger in ["buy-button-2", "sell-button-2"]:
        if not current_ticker:
            return (
                is_open,
                current_ticker,
                no_update,
                "No ticker selected.",
                "warning",
                True,
                no_update
            )

        try:
            price = float(price)
            quantity = float(quantity)
        except (TypeError, ValueError):
            return (
                is_open,
                current_ticker,
                no_update,
                "Invalid price or quantity.",
                "danger",
                True,
                no_update
            )

        if price <= 0 or quantity <= 0:
            return (
                is_open,
                current_ticker,
                no_update,
                "Price and quantity must be positive.",
                "warning",
                True,
                no_update
            )

        user = User.query.get(current_user.id)
        if user is None:
            return (
                is_open,
                current_ticker,
                no_update,
                "User not found.",
                "danger",
                True,
                no_update
            )

        ticker = current_ticker.upper()

        try:
            if trigger == "buy-button-2":
                cost = price * quantity
                if user.balance < cost:
                    return (
                        is_open,
                        current_ticker,
                        no_update,
                        "Insufficient balance.",
                        "warning",
                        True,
                        no_update
                    )

                holding = StockHolding.query.filter_by(
                    user_id=user.id, ticker=ticker
                ).first()

                if holding:
                    total_cost = holding.shares * holding.avg_price + cost
                    holding.shares += quantity
                    holding.avg_price = total_cost / holding.shares
                else:
                    db.session.add(
                        StockHolding(
                            user_id=user.id,
                            ticker=ticker,
                            shares=quantity,
                            avg_price=price
                        )
                    )

                user.balance -= cost
                db.session.commit()

                return (
                    True,
                    current_ticker,
                    no_update,
                    f"Bought {quantity} {ticker} at ${price:.2f}",
                    "success",
                    True,
                    time.time()  # REFRESH SIGNAL
                )

            # ------------------ Sell ------------------
            holding = StockHolding.query.filter_by(
                user_id=user.id, ticker=ticker
            ).first()

            if holding is None or holding.shares < quantity:
                return (
                    is_open,
                    current_ticker,
                    no_update,
                    "Not enough shares to sell.",
                    "warning",
                    True,
                    no_update
                )

            proceeds = price * quantity
            holding.shares -= quantity

            if holding.shares <= 0:
                db.session.delete(holding)

            user.balance += proceeds
            db.session.commit()

            return (
                True,
                current_ticker,
                no_update,
                f"Sold {quantity} {ticker} at ${price:.2f}",
                "success",
                True,
                time.time()  # REFRESH SIGNAL
            )

        except Exception:
            db.session.rollback()
            return (
                is_open,
                current_ticker,
                no_update,
                "Transaction failed.",
                "danger",
                True,
                no_update
            )

    raise PreventUpdate


@callback(
    Output("trade-price-2", "value", allow_duplicate=True),
    Output("trade-price-2", "disabled"),
    Input("order-type-2", "value"),
    Input("trade-ticker-2", "children"),
    Input("trade-modal-2", "is_open"),
    prevent_initial_call=True
)
def handle_price_input(order_type, ticker, is_open):
    if not is_open or not ticker:
        raise PreventUpdate

    if order_type == "market-order":
        try:
            data = yf.Ticker(ticker).history(period="1d")
            latest_price = (
                round(float(data["Close"].iloc[-1]), 2)
                if not data.empty
                else None
            )
        except Exception:
            latest_price = None

        return latest_price, True

    # limit / stop-loss
    return no_update, False

@callback(
    Output("trade-amount-2", "children"),
    Input("trade-price-2", "value"),
    Input("trade-quantity-2", "value")
)   
def update_trade_amount_acc(price, quantity):
    # Prevent calculation if inputs are empty or None
    if price is None or quantity is None:
        return "0.00"

    try:
        # Calculate the total amount
        amount = float(price) * float(quantity)
        return f"{amount:,.2f}"
    except (TypeError, ValueError):
        return "0.00"