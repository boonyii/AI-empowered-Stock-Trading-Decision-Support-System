import yfinance as yf
import pandas as pd
import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score



def rf_model(data):

    data.reset_index(inplace = True)
    data.rename(columns = {'Date': 'Datetime'}, inplace = True)
    data.columns = data.columns.droplevel(1)
    data.columns.name = None
    data.index = pd.to_datetime(data['Datetime'])
    data = data.drop(['Datetime'], axis = 'columns')

    data["Tomorrow"] = data["Close"].shift(-1)

    data["Target"] = (data["Tomorrow"] > data["Close"]).astype(int)
    data = data.iloc[:-1].copy()

    model = RandomForestClassifier(n_estimators = 100, min_samples_split = 100, random_state = 1)

    split = int(len(data) * 0.8)

    train = data.iloc[:split]
    test = data.iloc[split:]


    predictors = ["Close", "Volume", "Open", "High", "Low"]
    model.fit(train[predictors], train["Target"])


    preds = model.predict(test[predictors])
    preds = pd.Series(preds, index = test.index, name = "Predicted")  
    precision = precision_score(test["Target"], preds)

    combined = pd.concat(
        [test["Target"].rename("Actual"), preds],
        axis=1
    )

    latest_row = data.iloc[[-1]][predictors]   
    next_day_direction = model.predict(latest_row)[0]


    return precision, next_day_direction, combined

