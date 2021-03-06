from dataLoader import *
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import metrics
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Dropout, Dense, Activation
from tensorflow.keras.callbacks import ModelCheckpoint

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
tf.config.experimental.set_memory_growth(tf.config.experimental.list_physical_devices('GPU')[0], True)
DATANAME = 'CH_MNIST'
TARGET_MODEL_GENRE = 'ResNet'
SHADOW_MODEL_GENRE = 'ResNet'
EPOCHS = 40
BATCH_SIZE = 64
NUM_CLASSES = 1
LEARNING_RATE = 5e-5
NN_ATTACK_WEIGHTS_PATH = "weights/NN_Attack/DIFF_NN_Attack_{}_{}.hdf5".format(DATANAME, SHADOW_MODEL_GENRE)
TARGET_WEIGHTS_PATH = "weights/Target/{}_{}.hdf5".format(DATANAME, TARGET_MODEL_GENRE)
SHADOW_WEIGHTS_PATH = "weights/DistributionShadow/Diff_{}_{}.hdf5".format(DATANAME, TARGET_MODEL_GENRE)

(x_train_sha, y_train_sha), (x_test_sha, y_test_sha), m_train = globals()['load_Diff_' + DATANAME]('ShadowModel')
Shadow_Model = load_model(SHADOW_WEIGHTS_PATH)
c_train = np.sort(Shadow_Model.predict(np.r_[x_train_sha, x_test_sha]), axis=1)[:, ::-1]

(x_train_tar, y_train_tar), (x_test_tar, y_test_tar), m_test = globals()['load_' + DATANAME]('TargetModel')
Target_Model = load_model(TARGET_WEIGHTS_PATH)
c_test = np.sort(Target_Model.predict(np.r_[x_train_tar, x_test_tar]), axis=1)[:, ::-1]

def create_attack_model(input_dim, num_classes=NUM_CLASSES):
    model = tf.keras.Sequential([
        Dense(512, input_dim=input_dim, activation='relu'),
        Dropout(0.2),
        Dense(256, activation='relu'),
        Dropout(0.2),
        Dense(128, activation='relu'),
        Dense(num_classes),
        Activation('sigmoid')
    ])
    model.summary()
    return model

def train(model, x_train, y_train):
    model.compile(loss='binary_crossentropy',
                  optimizer=keras.optimizers.Adam(lr=LEARNING_RATE),
                  metrics=[metrics.BinaryAccuracy(), metrics.Precision(), metrics.Recall()])
    checkpoint = ModelCheckpoint(NN_ATTACK_WEIGHTS_PATH, monitor='precision', verbose=1, save_best_only=True,
                                 mode='max')
    model.fit(x_train, y_train,
              epochs=EPOCHS,
              batch_size=BATCH_SIZE,
              callbacks=[checkpoint])


def evaluate(x_test, y_test):
    model = keras.models.load_model(NN_ATTACK_WEIGHTS_PATH)
    loss, accuracy, precision, recall = model.evaluate(x_test, y_test, verbose=1)
    F1_Score = 2 * (precision * recall) / (precision + recall)
    print('loss:%.4f accuracy:%.4f precision:%.4f recall:%.4f F1_Score:%.4f'
          % (loss, accuracy, precision, recall, F1_Score))


attackModel = create_attack_model(c_train.shape[1])
train(attackModel, c_train, m_train)
evaluate(c_test, m_test)