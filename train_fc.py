import purple.preprocessing.load_data as load_data
import purple.ml.fc as fc

import numpy as np
import pandas as pd

from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import tensorflow as tf


def weighted_roc_auc(y_true, y_pred, labels, weights_dict):
    unnorm_weights = np.array([weights_dict[label] for label in labels])
    weights = unnorm_weights / unnorm_weights.sum()
    classes_roc_auc = roc_auc_score(y_true, y_pred, labels=labels,
                                    multi_class="ovr", average=None)
    return sum(weights * classes_roc_auc)


data_path = "data/train_data.pqt"
train_df = pd.read_parquet(data_path)
labels, x, y = load_data.extract_features_labels(train_df, categorical_labels=False)

print("Соотношение меток в исходной выборке")
for l in labels:
    print(f"{l} - {np.sum(y == l) / y.shape[0]}")

print(x.shape)
print(y.shape)

x_train, x_val, y_train, y_val = train_test_split(x, y,
                                                  test_size=0.2,
                                                  random_state=42)

print("Соотношение меток в валидационной выборке")
for l in labels:
    print(f"{l} - {np.sum(y_val == l) / y_val.shape[0]}")

y_train = load_data.one_hot_encoder(y_train, labels)
y_val = load_data.one_hot_encoder(y_val, labels)

model = fc.FCClassifier(input_shape=x.shape[1])
model.compile(loss=tf.keras.losses.CategoricalCrossentropy(),
              optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
                    validation_data=(x_val, y_val),
                    epochs=10,
                    batch_size=4096)

cluster_weights = pd.read_excel("data/cluster_weights.xlsx").set_index("cluster")
weights_dict = cluster_weights["unnorm_weight"].to_dict()

y_pred_proba = model.predict(x_val)
print(y_pred_proba.shape)

print(weighted_roc_auc(y_val, y_pred_proba, labels, weights_dict))

