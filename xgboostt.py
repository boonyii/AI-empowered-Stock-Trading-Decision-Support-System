import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
from finta import TA
import yfinance as yf
import datetime
from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error

def train_test_split(data):
    data = data.values
    n = int(len(data)* (1 - 0.2))
    return data[:n], data[n:]

def xgb_predict(train, val):
    train = np.array(train)
    X, y = train[:, :-1], train[:,-1]
    model = XGBRegressor(objective = 'reg:squarederror', n_estimators = 750, colsample_bytree = 0.7, learning_rate = 0.05, max_depth = 3, gamma = 1)
    model.fit(X,y)
    val = np.array(val).reshape(1, -1)
    pred = model.predict(val)
    return pred[0]

def mape(actual, pred):
    actual, pred = np.array(actual), np.array(pred)
    mape = np.mean(np.abs((actual-pred)/actual))*100
    return mape

def validate(data):
    predictions = []
    train, test = train_test_split(data)
    history = [x for x in train]

    for i in range(len(test)):
        X_test, y_test = test[i, :-1], test[i, -1]
        pred = xgb_predict(history, X_test)
        predictions.append(pred)    

        history.append(test[i])

    error = np.sqrt(mean_squared_error(test[:, -1], predictions))
    MAPE = mape(test[:,-1], predictions)
    return error, MAPE, test[:, -1], predictions, test

def xgboost_model(data):
    data.reset_index(inplace = True)
    data.rename(columns={'Date': 'Datetime'}, inplace = True)
    data.columns = data.columns.droplevel(1)
    data.columns.name = None
    data.index = pd.to_datetime(data['Datetime'])
    data = data.drop(['Datetime'], axis='columns')

    data['SMA200'] = TA.SMA(data, 200)
    data['RSI'] = TA.RSI(data)
    data['ATR'] = TA.ATR(data)
    data['BBWidth'] = TA.BBWIDTH(data)
    data['Williams'] = TA.WILLIAMS(data)

    data = data.iloc[200:,:]

    data['target'] = data.Close.shift(-1)
    data.dropna(inplace = True)

    rmse, MAPE, y, pred, test = validate(data)

    pred = np.array(pred)
    test_pred = np.c_[test,pred]

    data_TP = pd.DataFrame(test_pred, columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA200', 'RSI', 'ATR', 'BBWidth', 'Williams', 'Target', 'Pred'])

    dates = data.index[-len(test):] 
    data_TP.index = dates

    return data_TP, rmse, MAPE