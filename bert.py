# -*- coding: utf-8 -*-
"""BERT.ipynb

Automatically generated by Colaboratory.
"""

!pip install transformers

import numpy as np
import pandas as pd
import tensorflow as tf
from transformers import TFBertModel, BertTokenizer
from google.colab import files
import warnings
warnings.filterwarnings('ignore')

uploaded = files.upload()

data = pd.read_csv('IMDB Dataset.csv')
data

from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
label_encoder.fit(data['sentiment'])
num_labels = len(label_encoder.classes_)

data['encoded_label'] = np.asarray(label_encoder.transform(data['sentiment']), dtype=np.int32)
data.head()

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

"""# Review Dataset BERT

## Train / Test Split
"""

texts = data['review'].to_list()
labels = data['encoded_label'].to_list()

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(texts, labels, random_state=42, test_size=0.2)

"""## Encoding"""

def encode(reviews, tokenizer):
  input_ids = []
  attention_masks = []
  token_type_ids = []
  # print(reviews)

  for sentence in reviews:
    # print(sentence)
    tokenized_sentence = tokenizer.encode_plus(sentence, 
                                           max_length = 100,
                                           add_special_tokens = True,
                                           pad_to_max_length = True,
                                           return_attention_mask = True,
                                           truncation = True)
    
    # print(tokenized_sentence)
    input_ids.append(tokenized_sentence['input_ids'])
    attention_masks.append(tokenized_sentence['attention_mask'])
    token_type_ids.append(tokenized_sentence['token_type_ids'])

  return input_ids, attention_masks, token_type_ids

#학습데이터 토큰화
train_input_ids, train_attention_masks, train_token_type_ids = encode(X_train, tokenizer)
 
#테스트데이터 토큰화
test_input_ids, test_attention_masks, test_token_type_ids = encode(X_test, tokenizer)

print(train_input_ids)
print(train_attention_masks)
print(train_token_type_ids)

def map_example_to_dict(input_ids, attention_masks, token_type_ids, label):
    return {
      "input_ids": input_ids,
      "token_type_ids": token_type_ids,
      "attention_mask": attention_masks,
      }, label

def data_encode(input_ids_list, attention_mask_list, token_type_ids_list, label_list):
    return tf.data.Dataset.from_tensor_slices((input_ids_list, attention_mask_list, token_type_ids_list, label_list)).map(map_example_to_dict)

BATCH_SIZE = 8
print(len(y_train))
 
#학습 데이터
train_data_encoded = data_encode(train_input_ids, train_attention_masks, train_token_type_ids, y_train).shuffle(10000).batch(BATCH_SIZE)
 
#평가 데이터
test_data_encoded = data_encode(test_input_ids, test_attention_masks, test_token_type_ids, y_test).batch(BATCH_SIZE)

"""## BERT Model (Binary Classification)


"""

from transformers.models.bert.modeling_tf_bert import TFBertForSequenceClassification
model = TFBertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels = 2
)

optimizer = tf.keras.optimizers.Adam(1e-5)
loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')
model.compile(optimizer=optimizer, loss=loss, metrics=[metric])

NUM_EPOCHS = 3
history = model.fit(train_data_encoded, epochs=NUM_EPOCHS, batch_size=BATCH_SIZE, validation_data=test_data_encoded)

import matplotlib.pyplot as plt
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.xlabel('epoch')
plt.ylabel('loss')
plt.legend(['train','val'])
plt.show()

plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.xlabel('epoch')
plt.ylabel('accuracy')
plt.legend(['train','val'])
plt.show()

"""##Cross Validation"""

from sklearn.model_selection import KFold
from transformers.models.bert.modeling_tf_bert import TFBertForSequenceClassification
import matplotlib.pyplot as plt

#5 folds for cross validation, each fold with different train, valid dataset

kf = KFold(n_splits=3, shuffle=True, random_state=42)
for train_idx, val_idx in kf.split(texts):
  #print(train_idx)
  X_train, X_test, y_train, y_test = train_test_split(texts, labels, random_state=42, test_size=0.2)
  #학습데이터 토큰화
  train_input_ids, train_attention_masks, train_token_type_ids = encode(X_train, tokenizer)
  
  #테스트데이터 토큰화
  test_input_ids, test_attention_masks, test_token_type_ids = encode(X_test, tokenizer)

  BATCH_SIZE = 8
  #print(len(y_train))
  
  #학습 데이터
  train_data_encoded = data_encode(train_input_ids, train_attention_masks, train_token_type_ids, y_train).shuffle(10000).batch(BATCH_SIZE)
  
  #평가 데이터
  test_data_encoded = data_encode(test_input_ids, test_attention_masks, test_token_type_ids, y_test).batch(BATCH_SIZE)

  model = TFBertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels = 2
  )
  optimizer = tf.keras.optimizers.Adam(1e-5)
  loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
  metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')
  model.compile(optimizer=optimizer, loss=loss, metrics=[metric])

  NUM_EPOCHS = 7
  k_fold_history = model.fit(train_data_encoded, epochs=NUM_EPOCHS, batch_size=BATCH_SIZE, validation_data=test_data_encoded)
  plt.plot(k_fold_history.history['accuracy'])
  plt.plot(k_fold_history.history['val_accuracy'])
  plt.xlabel('epoch')
  plt.ylabel('accuracy')
  plt.legend(['train','val'])
  plt.show()

plt.plot(k_fold_history.history['loss'])
plt.plot(k_fold_history.history['val_loss'])
plt.xlabel('epoch')
plt.ylabel('loss')
plt.legend(['train','val'])
plt.show()

plt.plot(k_fold_history.history['accuracy'])
plt.plot(k_fold_history.history['val_accuracy'])
plt.xlabel('epoch')
plt.ylabel('accuracy')
plt.legend(['train','val'])
plt.show()

import re
id2labels = model.config.id2label
model.config.id2label = {id : label_encoder.inverse_transform([int(re.sub('LABEL_', '', label))])[0]  for id, label in id2labels.items()}

label2ids = model.config.label2id
model.config.label2id = {label_encoder.inverse_transform([int(re.sub('LABEL_', '', label))])[0] : id   for id, label in id2labels.items()}

id2labels

import os
MODEL_NAME = 'fine-tuned-bert-base'
MODEL_SAVE_PATH = os.path.join("_model", MODEL_NAME) # change this to your preferred location

if os.path.exists(MODEL_SAVE_PATH):
    print(f"{MODEL_SAVE_PATH} -- Folder already exists \n")
else:
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    print(f"{MODEL_SAVE_PATH} -- Folder create complete \n")

# save tokenizer, model
model.save_pretrained(MODEL_SAVE_PATH)
tokenizer.save_pretrained(MODEL_SAVE_PATH)

"""## Test"""

uploaded = files.upload()

total_data = pd.read_csv('movie_data.csv')
total_data

from transformers import TextClassificationPipeline

# Load Fine-tuning model
loaded_tokenizer = BertTokenizer.from_pretrained(MODEL_SAVE_PATH)
loaded_model = TFBertForSequenceClassification.from_pretrained(MODEL_SAVE_PATH)

text_classifier = TextClassificationPipeline(
    tokenizer=loaded_tokenizer, 
    model=loaded_model, 
    framework='tf',
    return_all_scores=True
)

predicted_label_list = []
predicted_score_list = []

for text in total_data['Review']:
    # predict
    preds_list = text_classifier(text)[0]

    sorted_preds_list = sorted(preds_list, key=lambda x: x['score'], reverse=True)
    if sorted_preds_list[0]['label'] == 'positive':
      predicted_label_list.append('positive')
    else:
      predicted_label_list.append('negative')
    predicted_score_list.append(sorted_preds_list[0]['score'])
total_data['pred'] = predicted_label_list
total_data['score'] = predicted_score_list
total_data.head()

total_data

from sklearn.metrics import classification_report

print(classification_report(y_true=total_data['Pos/Neg'], y_pred=total_data['pred']))

"""# BERT Emotion (multi-classifier)"""

uploaded = files.upload()

emotion_data = pd.read_csv('small_plot.csv')
emotion_data

s = 0.0
for i in emotion_data['overview']:
    word_list = i.split()
    s = s + len(word_list)
print("Average length of each plot : ",s/emotion_data.shape[0])
happy = len(emotion_data.loc[emotion_data['emotion'] == 'happy'])
sad = len(emotion_data.loc[emotion_data['emotion'] == 'sad'])
fear = len(emotion_data.loc[emotion_data['emotion'] == 'fear'])
thrill = len(emotion_data.loc[emotion_data['emotion'] == 'thrill'])

print(happy, sad,  fear, thrill)

# for i in range(data.shape[0]):
#     if data.iloc[i]['happiness'] == 1:
#         happy = happy + 1
#     if data.iloc[i]['sadness'] == 1:
#         sad = sad + 1
#     if data.iloc[i]['fear'] == 1:
#         fear = fear + 1
#     if data.iloc[i]['angry'] == 1:
#         angry = angry + 1

print("Percentage of plots with happy is "+str(happy/emotion_data.shape[0]*100)+"%")
print("Percentage of plots with sad is "+str(sad/emotion_data.shape[0]*100)+"%")
print("Percentage of plots with fear is "+str(fear/emotion_data.shape[0]*100)+"%")
print("Percentage of plots with thrill is "+str(thrill/emotion_data.shape[0]*100)+"%")

from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
label_encoder.fit(emotion_data['emotion'])
num_labels = len(label_encoder.classes_)

emotion_data['encoded_label'] = np.asarray(label_encoder.transform(emotion_data['emotion']), dtype=np.int32)
emotion_data.head()

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

"""## Train / Test Split"""

texts = emotion_data['overview'].to_list()
labels = emotion_data['encoded_label'].to_list()

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(texts, labels, random_state=42, test_size=0.2)

"""## Encoding"""

def emotion_encode(plots, tokenizer):
  input_ids = []
  attention_masks = []
  token_type_ids = []
  # print(reviews)

  for sentence in plots:
    # print(sentence)
    tokenized_sentence = tokenizer.encode_plus(sentence, 
                                           max_length = 20,
                                           add_special_tokens = True,
                                           pad_to_max_length = True,
                                           return_attention_mask = True,
                                           truncation = True)
    
    # print(tokenized_sentence)
    input_ids.append(tokenized_sentence['input_ids'])
    attention_masks.append(tokenized_sentence['attention_mask'])
    token_type_ids.append(tokenized_sentence['token_type_ids'])

  return input_ids, attention_masks, token_type_ids

#학습데이터 토큰화
train_input_ids, train_attention_masks, train_token_type_ids = emotion_encode(X_train, tokenizer)
 
#테스트데이터 토큰화
test_input_ids, test_attention_masks, test_token_type_ids = emotion_encode(X_test, tokenizer)

print(train_input_ids)
print(train_attention_masks)
print(train_token_type_ids)

def map_example_to_dict(input_ids, attention_masks, token_type_ids, label):
    return {
      "input_ids": input_ids,
      "token_type_ids": token_type_ids,
      "attention_mask": attention_masks,
      }, label

def data_encode(input_ids_list, attention_mask_list, token_type_ids_list, label_list):
    return tf.data.Dataset.from_tensor_slices((input_ids_list, attention_mask_list, token_type_ids_list, label_list)).map(map_example_to_dict)

BATCH_SIZE = 32
print(len(y_train))
 
#학습 데이터
train_data_encoded = data_encode(train_input_ids, train_attention_masks, train_token_type_ids, y_train).shuffle(10000).batch(BATCH_SIZE)
 
#평가 데이터
test_data_encoded = data_encode(test_input_ids, test_attention_masks, test_token_type_ids, y_test).batch(BATCH_SIZE)

"""## Model"""

from transformers.models.bert.modeling_tf_bert import TFBertForSequenceClassification
model = TFBertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels = 4
)

optimizer = tf.keras.optimizers.Adam(1e-5)
loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')
model.compile(optimizer=optimizer, loss=loss, metrics=[metric])

NUM_EPOCHS = 15
emotion_history = model.fit(train_data_encoded, epochs=NUM_EPOCHS, batch_size=BATCH_SIZE, validation_data=test_data_encoded)

import matplotlib.pyplot as plt
plt.plot(emotion_history.history['loss'])
plt.plot(emotion_history.history['val_loss'])
plt.xlabel('epoch')
plt.ylabel('loss')
plt.legend(['train','val'])
plt.show()

plt.plot(emotion_history.history['accuracy'])
plt.plot(emotion_history.history['val_accuracy'])
plt.xlabel('epoch')
plt.ylabel('accuracy')
plt.legend(['train','val'])
plt.show()

max_val = 0
max_idx = 0
idx = 0
for acc in emotion_history.history['val_accuracy']:
  if max_val < acc:
    max_val = acc
    max_idx = idx
  idx+=1
print(max_idx + 1, max_val)

"""## Cross Validation"""

from sklearn.model_selection import KFold

kf = KFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in kf.split(texts):
  X_train, X_test, y_train, y_test = train_test_split(texts, labels, random_state=42, test_size=0.2)
  #학습데이터 토큰화
  train_input_ids, train_attention_masks, train_token_type_ids = emotion_encode(X_train, tokenizer)
  
  #테스트데이터 토큰화
  test_input_ids, test_attention_masks, test_token_type_ids = emotion_encode(X_test, tokenizer)
  
  BATCH_SIZE = 32
  #print(len(y_train))
  
  #학습 데이터
  train_data_encoded = data_encode(train_input_ids, train_attention_masks, train_token_type_ids, y_train).shuffle(10000).batch(BATCH_SIZE)
  
  #평가 데이터
  test_data_encoded = data_encode(test_input_ids, test_attention_masks, test_token_type_ids, y_test).batch(BATCH_SIZE)
  model = TFBertForSequenceClassification.from_pretrained(
      "bert-base-uncased",
      num_labels = 4
  )
  optimizer = tf.keras.optimizers.Adam(1e-5)
  loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
  metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')
  model.compile(optimizer=optimizer, loss=loss, metrics=[metric])

  NUM_EPOCHS = 10
  emotion_history = model.fit(train_data_encoded, epochs=NUM_EPOCHS, batch_size=BATCH_SIZE, validation_data=test_data_encoded)

import matplotlib.pyplot as plt
plt.plot(emotion_history.history['loss'])
plt.plot(emotion_history.history['val_loss'])
plt.xlabel('epoch')
plt.ylabel('loss')
plt.legend(['train','val'])
plt.show()

plt.plot(emotion_history.history['accuracy'])
plt.plot(emotion_history.history['val_accuracy'])
plt.xlabel('epoch')
plt.ylabel('accuracy')
plt.legend(['train','val'])
plt.show()

"""## SAVE MODEL"""

import re
id2labels = model.config.id2label
model.config.id2label = {id : label_encoder.inverse_transform([int(re.sub('LABEL_', '', label))])[0]  for id, label in id2labels.items()}

label2ids = model.config.label2id
model.config.label2id = {label_encoder.inverse_transform([int(re.sub('LABEL_', '', label))])[0] : id   for id, label in id2labels.items()}

label2ids

import os
MODEL_NAME = 'fine-tuned-bert-base'
MODEL_SAVE_PATH = os.path.join("_model", MODEL_NAME) # change this to your preferred location

if os.path.exists(MODEL_SAVE_PATH):
    print(f"{MODEL_SAVE_PATH} -- Folder already exists \n")
else:
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    print(f"{MODEL_SAVE_PATH} -- Folder create complete \n")

# save tokenizer, model
model.save_pretrained(MODEL_SAVE_PATH)
tokenizer.save_pretrained(MODEL_SAVE_PATH)

"""## Test"""

total_data

from transformers import TextClassificationPipeline

# Load Fine-tuning model
loaded_tokenizer = BertTokenizer.from_pretrained(MODEL_SAVE_PATH)
loaded_model = TFBertForSequenceClassification.from_pretrained(MODEL_SAVE_PATH)

text_classifier = TextClassificationPipeline(
    tokenizer=loaded_tokenizer, 
    model=loaded_model, 
    framework='tf',
    return_all_scores=True
)

predicted_label_list = []
predicted_score_list = []

for text in total_data['Plot']:
    # predict
    preds_list = text_classifier(text)[0]

    sorted_preds_list = sorted(preds_list, key=lambda x: x['score'], reverse=True)
    if sorted_preds_list[0]['label'] == 'happy':
      predicted_label_list.append('happy')
    elif sorted_preds_list[0]['label'] == 'sad':
      predicted_label_list.append('sad')
    elif sorted_preds_list[0]['label'] == 'fear':
      predicted_label_list.append('fear')
    else:
      predicted_label_list.append('thrill')
    predicted_score_list.append(sorted_preds_list[0]['score'])
total_data['emotion_pred'] = predicted_label_list
total_data['emotion_score'] = predicted_score_list
total_data.head()

from sklearn.metrics import classification_report

print(classification_report(y_true=total_data['Emotion'], y_pred=total_data['emotion_pred']))

total_data

"""## Recommendation"""

total_data.to_csv('predicted.csv', index=False)

pred_data = pd.read_csv('predicted.csv')

pred_data

import random
NUM_MOVIES_SEEN = 5
RAND = random.randint(1, 100)
seen_movies = pred_data.sample(frac=1, random_state=RAND).reset_index(drop=True).head(NUM_MOVIES_SEEN)
seen_movies

happy_score = 0.0
sad_score = 0.0
fear_score = 0.0
thrill_score = 0.0
for i in range(NUM_MOVIES_SEEN):
  if seen_movies['emotion_pred'][i] == 'happy':
    happy_score += seen_movies['emotion_score'][i]
  elif seen_movies['emotion_pred'][i] == 'sad':
    sad_score += seen_movies['emotion_score'][i]
  elif seen_movies['emotion_pred'][i] == 'fear':
    fear_score += seen_movies['emotion_score'][i]
  elif seen_movies['emotion_pred'][i] == 'thrill':
    thrill_score += seen_movies['emotion_score'][i]

print(happy_score, sad_score, fear_score, thrill_score)
emotion_scores = [happy_score, sad_score, fear_score, thrill_score]
if max(emotion_scores) == happy_score:
  max_emotion = 'happy'
elif max(emotion_scores) == sad_score:
  max_emotion = 'sad'
elif max(emotion_scores) == fear_score:
  max_emotion = 'fear'
elif max(emotion_scores) == thrill_score:
  max_emotion = 'thrill'

print(max_emotion)

pred_data_copy = pred_data
for i in range(NUM_MOVIES_SEEN):
  pred_data_copy = pred_data_copy.drop(pred_data_copy[pred_data_copy['Movie'] == seen_movies['Movie'][i]].index).reset_index(drop=True)

pred_data_copy

"""## Random Recommendation"""

pred_emotion_data = pred_data_copy[pred_data_copy['emotion_pred'] == max_emotion].reset_index(drop=True)
pred_emotion_data

NUM_RECOMMEND_MOVIES = 5
RAND = random.randint(1, 100)
recommend_movies = pred_emotion_data.sample(frac=1, random_state=RAND).reset_index(drop=True).head(NUM_RECOMMEND_MOVIES)

recommend_movies

for i in range(NUM_RECOMMEND_MOVIES):
  print('Movie Recommendataion #' + str(i + 1) + ': ' + recommend_movies['Movie'][i])

"""## Recommendation based on review score"""

pred_emotion_data = pred_data_copy[pred_data_copy['emotion_pred'] == max_emotion].reset_index(drop=True)
pred_emotion_data

NUM_RECOMMEND_MOVIES = 5
recommend_movies = pred_emotion_data.sort_values(by='score', ascending=False).head(NUM_RECOMMEND_MOVIES).reset_index(drop=True)
recommend_movies

for i in range(NUM_RECOMMEND_MOVIES):
  print('Movie Recommendataion #' + str(i + 1) + ': ' + recommend_movies['Movie'][i])

"""## Using Selected Seen Movies"""

pred_data = pd.read_csv('predicted.csv')
pred_data

seen_movies_list = ['Regeneration', 'CHILDREN OF HEAVEN', 'Day Shift', 'Land of the Dead', 'Silent Night']

happy_score = 0.0
sad_score = 0.0
fear_score = 0.0
thrill_score = 0.0
for text in seen_movies_list:
  emotion_string = pred_data[pred_data['Movie'] == text]['emotion_pred'].values[0]
  emotion_score_value = pred_data[pred_data['Movie'] == text]['emotion_score'].values[0]
  if emotion_string == 'happy':
    happy_score += emotion_score_value
  elif emotion_string == 'sad':
    sad_score += emotion_score_value
  elif emotion_string == 'fear':
    fear_score += emotion_score_value
  elif emotion_string == 'thrill':
    thrill_score += emotion_score_value

print(happy_score, sad_score, fear_score, thrill_score)
emotion_scores = [happy_score, sad_score, fear_score, thrill_score]
if max(emotion_scores) == happy_score:
  max_emotion = 'happy'
elif max(emotion_scores) == sad_score:
  max_emotion = 'sad'
elif max(emotion_scores) == fear_score:
  max_emotion = 'fear'
elif max(emotion_scores) == thrill_score:
  max_emotion = 'thrill'

print(max_emotion)

pred_data_copy = pred_data
for text in seen_movies_list:
  pred_data_copy = pred_data_copy.drop(pred_data_copy[pred_data_copy['Movie'] == text].index).reset_index(drop=True)

pred_data_copy

"""## Random Recommendation"""

pred_emotion_data = pred_data_copy[pred_data_copy['emotion_pred'] == max_emotion].reset_index(drop=True)
pred_emotion_data

import random
NUM_RECOMMEND_MOVIES = 5
RAND = random.randint(1, 100)
recommend_movies = pred_emotion_data.sample(frac=1, random_state=RAND).reset_index(drop=True).head(NUM_RECOMMEND_MOVIES)

recommend_movies

for i in range(NUM_RECOMMEND_MOVIES):
  print('Movie Recommendataion #' + str(i + 1) + ': ' + recommend_movies['Movie'][i])

"""## Recommendation based on review score"""

pred_emotion_data = pred_data_copy[pred_data_copy['emotion_pred'] == max_emotion].reset_index(drop=True)
pred_emotion_data

NUM_RECOMMEND_MOVIES = 5
recommend_movies = pred_emotion_data.sort_values(by='score', ascending=False).head(NUM_RECOMMEND_MOVIES).reset_index(drop=True)
recommend_movies

for i in range(NUM_RECOMMEND_MOVIES):
  print('Movie Recommendataion #' + str(i + 1) + ': ' + recommend_movies['Movie'][i])

"""##Emotion score + Review score"""

pred_emotion_data = pred_data_copy[pred_data_copy['emotion_pred'] == max_emotion].reset_index(drop=True)
pred_emotion_data

alpha = 0.5
score_list = []

for i in range(len(pred_emotion_data["score"])):
  total_score = alpha * pred_emotion_data["score"][i] + (1-alpha) * pred_emotion_data["emotion_score"][i]
  score_list.append(total_score)
pred_emotion_data["total_score"] = score_list 
pred_emotion_data

NUM_RECOMMEND_MOVIES = 5
recommend_movies = pred_emotion_data.sort_values(by='total_score', ascending=False).head(NUM_RECOMMEND_MOVIES).reset_index(drop=True)
recommend_movies

for i in range(NUM_RECOMMEND_MOVIES):
  print('Movie Recommendataion #' + str(i + 1) + ': ' + recommend_movies['Movie'][i])