from pandas import read_csv, Series
from datetime import datetime
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.models import Model
from pandas import concat

def get_train_test_dataset(apikey_normalized_data_file, client):
    dataset = read_csv(apikey_normalized_data_file, header=0, index_col=0, parse_dates=True)
    dataset = series_to_supervised(dataset)
    train = dataset[client["train"]["start"]:client["train"]["end"]]
    test = dataset[:client["train"]["start"]]
    test.append(dataset[client["train"]["end"]:])
    return train, test

# convert series to supervised learning
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
	n_vars = 1 if type(data) is list else data.shape[1]
	df = data
	cols, names = list(), list()
	# input sequence (t-n, ... t-1)
	for i in range(n_in, 0, -1):
		cols.append(df.shift(i))
		names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
	# forecast sequence (t, t+1, ... t+n)
	for i in range(0, n_out):
		cols.append(df.shift(-i))
		if i == 0:
			names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
		else:
			names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
	# put it all together
	agg = concat(cols, axis=1)
	agg.columns = names
	# drop rows with NaN values
	if dropnan:
		agg.dropna(inplace=True)
	return agg

def get_autoencoder(data, encoding_dimension, step = 250):
	dim = data.shape[0]
	data = Input(shape=(data.shape[1], data.shape[2]))
	encoded = data

	# Encoded layers
	for value in range((dim - step), encoding_dimension, -step):
		encoded = Dense(value, activation="relu")(encoded)

	decoded = Dense(encoding_dimension, activation="relu")(encoded)

	# Decoded layers
	for value in range(encoding_dimension, (dim + step), step):
		decoded = Dense(value, activation="relu")(decoded)

	autoencoder = Model(inputs=data, outputs=decoded)
	autoencoder.compile(optimizer="adadelta", loss="binary_crossentropy")
	autoencoder.summary()

	return autoencoder