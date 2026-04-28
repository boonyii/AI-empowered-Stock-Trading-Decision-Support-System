import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import datetime



def lstm_model(data):

    #############################################
    ########## Step 2: Preprocess Data ##########
    #############################################

    # Initialize MinMaxScaler to normalize the data between 0 and 1
    scaler = MinMaxScaler(feature_range=(0,1))

    # Scale the data for training
    scaled_data = scaler.fit_transform(data)



    ###################################################
    ########## Step 3: Prepare Training Data ##########
    ###################################################

    ###############
    #training_data_len = int(np.ceil(len(scaled_data) * 0.8))
    #train_data = scaled_data[0:training_data_len, :]
    ###############

    # 80% training, 10% validation, 10% testing
    total_len = len(scaled_data)
    train_size = int(np.ceil(total_len * 0.8))   
    val_size = int(np.ceil(total_len * 0.1))    

    train_data = scaled_data[:train_size]
    val_data = scaled_data[train_size - 60 : train_size + val_size]  
    test_data = scaled_data[train_size + val_size - 60 :]

    # Create empty lists for features (x_train) and target (y_train)
    x_train = []
    y_train = []

    # Populate x_train with 60 days of data and y_train with the following day’s closing price
    for i in range(60, len(train_data)):
        x_train.append(train_data[i-60:i, 0])  # Past 60 days
        y_train.append(train_data[i, 0])       # Target: the next day’s close price

    # Convert lists to numpy arrays for model training
    x_train, y_train = np.array(x_train), np.array(y_train)

    # Reshape x_train to the format [samples, time steps, features] required for LSTM
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))



    ##############################################
    ########## Step 4: Build LSTM Model ##########
    ##############################################

    model = Sequential()
    # First LSTM layer with 50 units and return sequences
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(Dropout(0.2))  # Dropout layer to prevent overfitting
    # Second LSTM layer
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))  # Dropout layer to prevent overfitting
    # Dense layer with 25 units
    model.add(Dense(units=25))
    # Output layer with 1 unit (the predicted price)
    model.add(Dense(units=1))

    # Compile the model using Adam optimizer and mean squared error as the loss function
    model.compile(optimizer='adam', loss='mean_squared_error')

    ###############
    # Stronger model but need more data to prevent overfitting

    #model = Sequential()
    #model.add(LSTM(units=100, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    #model.add(Dropout(0.2))  
    #model.add(LSTM(units=100, return_sequences=True))
    #model.add(Dropout(0.2))  
    #model.add(LSTM(units=100, return_sequences=True))
    #model.add(Dropout(0.2))  
    #model.add(LSTM(units=100, return_sequences=Fal))
    #model.add(Dropout(0.2))  
    #model.add(Dense(units=1))
    #model.compile(optimizer='adam', loss='mean_squared_error')
    ###############



    #############################################
    ########## Step 5: Train the Model ##########
    #############################################

    model.fit(x_train, y_train, batch_size=32, epochs=20, verbose=2)

    train_predictions = model.predict(x_train).flatten()

    # Inverse transform the predictions and actual values to original scale
    #train_predictions = scaler.inverse_transform(np.array(train_predictions).reshape(-1, 1))
    #y_train.inverse_transform(np.array(y_train).reshape(-1, 1))

    #plt.plot(train_predictions)
    #plt.plot(y_train)
    #plt.legend(['train_predictions','y_train'])

    #fig1 = go.Figure()
    #fig1.add_trace(go.Scatter(y=train_predictions, mode="lines", name="train_predictions"))
    #fig1.add_trace(go.Scatter(y=y_train,           mode="lines", name="y_train"))

    ################################################
    ########## Step 6: Validate the Model ##########
    ################################################

    x_val = []
    y_val = []

    for i in range(60, len(val_data)):
        x_val.append(val_data[i-60:i, 0])  
        y_val.append(val_data[i, 0])       

    x_val, y_val = np.array(x_val), np.array(y_val)

    x_val = np.reshape(x_val, (x_val.shape[0], x_val.shape[1], 1))

    val_predictions = model.predict(x_val).flatten()



    ############################################
    ########## Step 7: Test the Model ##########
    ############################################

    x_test = []
    y_test = []

    for i in range(60, len(test_data)):
        x_test.append(test_data[i-60:i, 0])  
        y_test.append(test_data[i, 0])       

    x_test, y_test = np.array(x_test), np.array(y_test)

    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    test_predictions = model.predict(x_test).flatten()



    ##############################################################
    ########## Step 8: Prepare Data for Future Forecast ##########
    ##############################################################

    # Take the last 60 days from the dataset for generating future predictions
    last_60_days = scaled_data[-60:]
    # Reshape last_60_days to fit the model input shape (1 sample, 60 timesteps, 1 feature)
    x_future = last_60_days.reshape((1, last_60_days.shape[0], 1))



    ######################################################
    ########### Step 9: Generate n-Day Forecast ##########
    ######################################################

    ################ For multiple days prediction 
    # Create an empty list to store predictions for the next 30 days
    #future_predictions = []
    #for _ in range(30):  # Change 30 to 60 to predict for 60 days
        # Predict the next day’s closing price based on the last 60 days
        #pred = model.predict(x_future)
        #future_predictions.append(pred[0, 0])  # Add prediction to the list
        
        # Update x_future with the new prediction by removing the first value and adding the new prediction
        #x_future = np.append(x_future[:, 1:, :], [[pred[0]]], axis=1)
    ###############

    # Predict the next day's closing price
    next_day_scaled = model.predict(x_future)



    ###########################################################################
    ########## Step 10: Transform Predictions Back to Original Scale ##########
    ###########################################################################

    # Convert the scaled predictions back to the original scale using inverse_transform
    # future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))
    next_day_price = scaler.inverse_transform(next_day_scaled)[0, 0]

    past_30_dates = data.index[-30:]

    # Create a DataFrame for visualization
    past_prices = data['Close'].iloc[-30:].copy()
    next_day_date = data.index[-1] + pd.Timedelta(days=1)
 
    return (
        train_predictions, y_train,
        val_predictions, y_val,
        test_predictions, y_test,
        past_30_dates, past_prices,
        next_day_date, next_day_price
    )

