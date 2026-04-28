import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import datetime
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score


def svm_model(data):

    data.reset_index(inplace = True)
    data.rename(columns = {'Date': 'Datetime'}, inplace = True)
    data.columns = data.columns.droplevel(1)
    data.columns.name = None
    data.index = pd.to_datetime(data['Datetime'])
    data = data.drop(['Datetime'], axis='columns')

    # Create predictor variables
    data['Open-Close'] = data.Open - data.Close
    data['High-Low'] = data.High - data.Low

    # Store all predictor variables in a variable X
    X = data[['Open-Close', 'High-Low']]

    y = np.where(data['Close'].shift(-1) > data['Close'], 1, 0)

    split_percentage = 0.8
    split = int(split_percentage*len(data))

    # Train data set
    X_train = X[:split]
    y_train = y[:split]

    # Test data set
    X_test = X[split:]
    y_test = y[split:]

    # Support vector classifier
    cls = SVC(probability=True).fit(X_train, y_train)

    # Calculate training accuracy
    # how well the model fits the data it learned on
    train_accuracy = accuracy_score(y_train, cls.predict(X_train))

    # Calculate testing accuracy
    # how well it generalizes to unseen future data
    test_accuracy = accuracy_score(y_test, cls.predict(X_test))

    today_features = X.iloc[-1:].values
    tomorrow_signal = cls.predict(today_features)[0]

    #Get probability estimates
    proba = cls.predict_proba(today_features)[0]  # [Prob_down, Prob_up]
    prob_down = proba[0] * 100
    prob_up = proba[1] * 100

    data['Predicted_Signal'] = cls.predict(X)
    data['Return'] = data['Close'].pct_change()
    data['Strategy_Return'] = data['Return'] * data['Predicted_Signal'].shift(1)

    data['Cum_Ret'] = data['Return'].cumsum()
    data['Cum_Strategy'] = data['Strategy_Return'].cumsum()

    return train_accuracy, test_accuracy, tomorrow_signal, prob_up, prob_down, data
