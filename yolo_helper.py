from keras.models import Sequential, Model
from keras.layers import Reshape, Activation, Conv2D, Input, MaxPooling2D, BatchNormalization, Flatten, Dense, Lambda, GlobalAveragePooling2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.merge import concatenate
import tensorflow as tf
from keras import backend as K

def PASCAL_VOC_bbox_2_yolo(bbox_orig, im_height, im_width, GRID_H = 13,  GRID_W = 13):
    width = (bbox_orig[2] - bbox_orig[0])/im_width
    height = (bbox_orig[3] - bbox_orig[1])/im_height
    center_x = bbox_orig[0]/im_width + width/2
    center_y = bbox_orig[1]/im_height + height/2
    
    in_grid_H_units = center_y*GRID_H
    in_grid_W_units = center_x*GRID_W
    in_grid_H = int(in_grid_H_units)
    in_grid_W = int(in_grid_W_units)
    center_H = in_grid_H_units - in_grid_H
    center_W = in_grid_W_units - in_grid_W
    norm_H = height*GRID_H
    norm_W = width*GRID_W
    return (in_grid_H, in_grid_W), [center_W, center_H, norm_W, norm_H]

def yolo_bbox_2_PASCAL_VOC(grid_coordinates, bbox_yolo, im_height, im_width, GRID_H, GRID_W):
    step_y = im_height/GRID_H
    step_x = im_width/GRID_W
    bb_width = bbox_yolo[2]*step_x
    bb_height = bbox_yolo[3]*step_y
    bb_left = (grid_coordinates[1] + bbox_yolo[0])*step_x - bb_width/2
    bb_top = (grid_coordinates[0] + bbox_yolo[1])*step_y - bb_height/2
    return bb_left, bb_top, bb_left+bb_width, bb_top+bb_height


# Esto solo hace un reshape particular antes de concatenar a la salida
def space_to_depth_x2(x):
    return tf.space_to_depth(x, block_size=2)

def get_YOLO_V2_NN(IMAGE_H, IMAGE_W, BOX, CLASS, GAP=False):
    input_image = Input(shape=(IMAGE_H, IMAGE_W, 3))

    # Layer 1
    x = Conv2D(32, (3,3), strides=(1,1), padding='same', name='conv_1', use_bias=False)(input_image)
    x = BatchNormalization(name='norm_1')(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # Layer 2
    x = Conv2D(64, (3,3), strides=(1,1), padding='same', name='conv_2', use_bias=False)(x)
    x = BatchNormalization(name='norm_2')(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # Layer 3
    x = Conv2D(128, (3,3), strides=(1,1), padding='same', name='conv_3', use_bias=False)(x)
    x = BatchNormalization(name='norm_3')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 4
    x = Conv2D(64, (1,1), strides=(1,1), padding='same', name='conv_4', use_bias=False)(x)
    x = BatchNormalization(name='norm_4')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 5
    x = Conv2D(128, (3,3), strides=(1,1), padding='same', name='conv_5', use_bias=False)(x)
    x = BatchNormalization(name='norm_5')(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # Layer 6
    x = Conv2D(256, (3,3), strides=(1,1), padding='same', name='conv_6', use_bias=False)(x)
    x = BatchNormalization(name='norm_6')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 7
    x = Conv2D(128, (1,1), strides=(1,1), padding='same', name='conv_7', use_bias=False)(x)
    x = BatchNormalization(name='norm_7')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 8
    x = Conv2D(256, (3,3), strides=(1,1), padding='same', name='conv_8', use_bias=False)(x)
    x = BatchNormalization(name='norm_8')(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # Layer 9
    x = Conv2D(512, (3,3), strides=(1,1), padding='same', name='conv_9', use_bias=False)(x)
    x = BatchNormalization(name='norm_9')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 10
    x = Conv2D(256, (1,1), strides=(1,1), padding='same', name='conv_10', use_bias=False)(x)
    x = BatchNormalization(name='norm_10')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 11
    x = Conv2D(512, (3,3), strides=(1,1), padding='same', name='conv_11', use_bias=False)(x)
    x = BatchNormalization(name='norm_11')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 12
    x = Conv2D(256, (1,1), strides=(1,1), padding='same', name='conv_12', use_bias=False)(x)
    x = BatchNormalization(name='norm_12')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 13
    x = Conv2D(512, (3,3), strides=(1,1), padding='same', name='conv_13', use_bias=False)(x)
    x = BatchNormalization(name='norm_13')(x)
    x = LeakyReLU(alpha=0.1)(x)

    skip_connection = x

    x = MaxPooling2D(pool_size=(2, 2))(x)

    # Layer 14
    x = Conv2D(1024, (3,3), strides=(1,1), padding='same', name='conv_14', use_bias=False)(x)
    x = BatchNormalization(name='norm_14')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 15
    x = Conv2D(512, (1,1), strides=(1,1), padding='same', name='conv_15', use_bias=False)(x)
    x = BatchNormalization(name='norm_15')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 16
    x = Conv2D(1024, (3,3), strides=(1,1), padding='same', name='conv_16', use_bias=False)(x)
    x = BatchNormalization(name='norm_16')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 17
    x = Conv2D(512, (1,1), strides=(1,1), padding='same', name='conv_17', use_bias=False)(x)
    x = BatchNormalization(name='norm_17')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 18
    x = Conv2D(1024, (3,3), strides=(1,1), padding='same', name='conv_18', use_bias=False)(x)
    x = BatchNormalization(name='norm_18')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 19
    x = Conv2D(1024, (3,3), strides=(1,1), padding='same', name='conv_19', use_bias=False)(x)
    x = BatchNormalization(name='norm_19')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 20
    x = Conv2D(1024, (3,3), strides=(1,1), padding='same', name='conv_20', use_bias=False)(x)
    x = BatchNormalization(name='norm_20')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 21
    skip_connection = Conv2D(64, (1,1), strides=(1,1), padding='same', name='conv_21', use_bias=False)(skip_connection)
    skip_connection = BatchNormalization(name='norm_21')(skip_connection)
    skip_connection = LeakyReLU(alpha=0.1)(skip_connection)
    skip_connection = Lambda(space_to_depth_x2)(skip_connection)

    x = concatenate([skip_connection, x])

    # Layer 22
    x = Conv2D(1024, (3,3), strides=(1,1), padding='same', name='conv_22', use_bias=False)(x)
    x = BatchNormalization(name='norm_22')(x)
    x = LeakyReLU(alpha=0.1)(x)

    # Layer 23
    x = Conv2D(BOX * (4 + 1 + CLASS), (1,1), strides=(1,1), padding='same', name='conv_23')(x)
    GRID_H_ = x.shape[1]
    GRID_W_ = x.shape[2]
    
    if GAP:
        output = GlobalAveragePooling2D(name='concatenated_outputs')(x)
        if BOX>1:
            output = Reshape((BOX, 4 + 1 + CLASS))(output)  
    else:
        output = Reshape((GRID_H_, GRID_W_, BOX, 4 + 1 + CLASS))(x)
    
    model = Model([input_image], output)
    return model

n_classes = 8
k_confidence = 1.0
k_classification = 1.0
k_bounding_boxes = 1.0

def set_loss_weights(k_conf = 1.0, k_class = 1.0, k_bboxes = 1.0):
    global k_confidence, k_classification, k_bounding_boxes
    k_confidence = k_conf
    k_classification = k_class
    k_bounding_boxes = k_bboxes

def set_classes(N = 6):
    global n_classes
    n_classes = N
    
def yolo_loss(y_true, y_pred):
    indexes = tf.where(K.equal(y_true[:,:,:,:,0], K.ones_like(y_true[:,:,:,:,0])))
    indexes_neg = tf.where(K.equal(y_true[:,:,:,:,0], K.zeros_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes)
    y_pred_pos = tf.gather_nd(y_pred, indexes)
    y_true_neg = tf.gather_nd(y_true, indexes_neg)
    y_pred_neg = tf.gather_nd(y_pred, indexes_neg)
    classes_cross_entropy = K.categorical_crossentropy(y_true_pos[:,1:1+n_classes], K.softmax(y_pred_pos[:,1:1+n_classes]))
    bounding_box_mse = K.mean(K.square(y_pred_pos[:,1+n_classes:1+n_classes+4] - y_true_pos[:,1+n_classes:1+n_classes+4]), axis=-1)
    confidence_cross_entropy_pos = K.mean(K.binary_crossentropy(y_true_pos[:,:1], K.sigmoid(y_pred_pos[:,:1])), axis=-1)
    confidence_cross_entropy_neg = 0.1*K.mean(K.binary_crossentropy(y_true_neg[:,:1], K.sigmoid(y_pred_neg[:,:1])), axis=-1)
    return k_classification*K.mean(classes_cross_entropy) + k_bounding_boxes*K.mean(bounding_box_mse) + k_confidence*K.mean(confidence_cross_entropy_pos) + K.mean(confidence_cross_entropy_neg)


def classes_acc(y_true, y_pred):
    indexes = tf.where(K.equal(y_true[:,:,:,:,0], K.ones_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes)
    y_pred_pos = tf.gather_nd(y_pred, indexes)
    return K.cast(K.equal(K.argmax(y_true_pos[:, 1:1+n_classes], axis=-1),
                          K.argmax(y_pred_pos[:, 1:1+n_classes], axis=-1)),
                  K.floatx())

def bounding_box_mse(y_true, y_pred):
    indexes = tf.where(K.equal(y_true[:,:,:,:,0], K.ones_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes)
    y_pred_pos = tf.gather_nd(y_pred, indexes)
    return K.mean(K.square(y_pred_pos[:,1+n_classes:1+n_classes+4] - y_true_pos[:,1+n_classes:1+n_classes+4]), axis=-1)

def confidence_acc_with_sigmoid(y_true, y_pred):
    indexes = tf.where(K.equal(y_true[:,:,:,:,0], K.ones_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes)
    y_pred_pos = tf.gather_nd(y_pred, indexes)
    return K.mean(K.equal(y_true_pos[:,:1], K.round(K.sigmoid(y_pred_pos[:,:1]))), axis=-1)


def positive_bin_cross_entropy_loss(y_true, y_pred):
    indexes = tf.where(K.equal(y_true[:,:,:,:,0], K.ones_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes)
    y_pred_pos = tf.gather_nd(y_pred, indexes)
    return K.mean(K.mean(K.binary_crossentropy(y_true_pos[:,:1], K.sigmoid(y_pred_pos[:,:1])), axis=-1))

def negative_bin_cross_entropy_loss(y_true, y_pred):
    indexes_neg = tf.where(K.equal(y_true[:,:,:,:,0], K.zeros_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes_neg)
    y_pred_pos = tf.gather_nd(y_pred, indexes_neg)
    return K.mean(K.mean(K.binary_crossentropy(y_true_pos[:,:1], K.sigmoid(y_pred_pos[:,:1])), axis=-1))

def categorical_cross_entropy_loss(y_true, y_pred):
    indexes = tf.where(K.equal(y_true[:,:,:,:,0], K.ones_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes)
    y_pred_pos = tf.gather_nd(y_pred, indexes)
    return K.mean(K.categorical_crossentropy(y_true_pos[:,1:1+n_classes], K.softmax(y_pred_pos[:,1:1+n_classes])))

def iou_metric(y_true, y_pred):
    indexes = tf.where(K.equal(y_true[:,:,:,:,0], K.ones_like(y_true[:,:,:,:,0])))
    y_true_pos = tf.gather_nd(y_true, indexes)
    y_pred_pos = tf.gather_nd(y_pred, indexes)
    boxA = y_true_pos[:,1+n_classes:1+n_classes+4]
    boxB = y_pred_pos[:,1+n_classes:1+n_classes+4]
    xA = K.stack([boxA[:,0]-boxA[:,2]/2, boxB[:,0]-boxB[:,2]/2], axis=-1)
    yA = K.stack([boxA[:,1]-boxA[:,3]/2, boxB[:,1]-boxB[:,3]/2], axis=-1)
    xB = K.stack([boxA[:,0]+boxA[:,2]/2, boxB[:,0]+boxB[:,2]/2], axis=-1)
    yB = K.stack([boxA[:,1]+boxA[:,3]/2, boxB[:,1]+boxB[:,3]/2], axis=-1)

    xA = K.max(xA, axis=-1)
    yA = K.max(yA, axis=-1)
    xB = K.min(xB, axis=-1)
    yB = K.min(yB, axis=-1)

    interX = K.zeros_like(xB)
    interY = K.zeros_like(yB)

    interX = K.stack([interX, xB-xA], axis=-1)
    interY = K.stack([interY, yB-yA], axis=-1)

    #because of these "max", interArea may be constant 0, without gradients, and you may have problems with no gradients. 
    interX = K.max(interX, axis=-1)
    interY = K.max(interY, axis=-1)
    interArea = interX * interY

    boxAArea = (boxA[:,2]) * (boxA[:,3])    
    boxBArea = (boxB[:,2]) * (boxB[:,3]) 
    iou = interArea / (boxAArea + boxBArea - interArea)
    return iou

import numpy as np
from  keras.utils import Sequence
from keras.preprocessing.image import ImageDataGenerator
from imgaug import augmenters as iaa
import imgaug as ia

class GeneratorMultipleOutputs(Sequence):
    def __init__(self, annotations_dict, folder, batch_size, target_size=(375, 500), GRID_H = 13, GRID_W = 13, BOX=1, classes=None, no_ext_idx=True, width_height_exp = False, flip_vertical=False, flip_horizontal=False):
        # flip = {no_flip, always, random}
        # concat_output: classes + bounding box + confidence, todo en unico np.array
        # no_ext_idx: los keys del anotation son el filename pero sin extención (Se lo tengo que quitar entonces)
        # width_height_exp: La bounding box viene con witdh y height en las posiciones 3 y 4. Eso es asi en COCO
        self.GRID_H = GRID_H
        self.GRID_W = GRID_W
        self.BOX = BOX
        self.width_height_exp = width_height_exp
        self.no_ext_idx = no_ext_idx
        np.random.seed(seed=40)
        self.annotations_dict = annotations_dict
        datagen = ImageDataGenerator(rescale=1./255, horizontal_flip=False)
        self.generator = datagen.flow_from_directory(
            classes = classes,
            directory=folder,
            target_size=target_size,
            color_mode="rgb",
            batch_size=batch_size,
            class_mode="categorical",
            shuffle=True,
            seed=42
        )
        self.idx_2_class_id = {v:k for k,v in self.generator.class_indices.items()}
        self.has_world = 'world' in self.generator.class_indices
        
        aug_oper = []
        if flip_horizontal:
            aug_oper.append(iaa.Fliplr(0.5))
        if flip_vertical:
            aug_oper.append(iaa.Flipud(0.5))
        # aug_oper.append(iaa.Crop(px=(0, 64)))
        self.seq = iaa.Sequential(aug_oper)
    
    def get_yolo_annotations(self, classes_onehot):
        N_classes = self.generator.num_classes
        batch_size = self.generator.batch_size
        # Indice de proximo batch
        batch_index = self.generator.batch_index
        if self.generator.batch_index == 0:
            # Esto indica el proximo batch, por lo tanto si esta en cero en realidad era el ultimo del epoch
            batch_index = self.__len__()
        # Hace shuffle por lo que queremos los indices del shuffle
        shuffle_indexes = self.generator.index_array
        # filename de cada imagen (corresponde a la key en el diccionario)
        batch_filenames = np.array(self.generator.filenames)[shuffle_indexes][(batch_index-1) * batch_size: batch_index*batch_size]
        # Obtengo classes
        classes = np.array(self.generator.classes)[self.generator.index_array][(batch_index-1) * batch_size:batch_index*batch_size]
        yolo_annotation_array = np.zeros([batch_size, self.GRID_H, self.GRID_W, self.BOX, 1 + N_classes + 4])
        keypoints_on_images = []
        for i, filename in enumerate(batch_filenames):
            class_id = self.idx_2_class_id[classes[i]]
            image_id = filename.split('/')[-1].split('.')[0]
            annot = self.annotations_dict[class_id][image_id]
            im_width = annot['width']
            im_height = annot['height']
            bbox = annot['bounding_boxes'][0]
            keypoints = [ia.Keypoint(x=bbox[0], y=bbox[1]), ia.Keypoint(x=bbox[2], y=bbox[3])]
            keypoints_on_images.append(ia.KeypointsOnImage(keypoints, (im_height, im_width, 3)))
        keypoints_aug = self.seq_det.augment_keypoints(keypoints_on_images)    
        for i, kp in enumerate(keypoints_aug):
            im_width = kp.shape[1]
            im_height = kp.shape[0]
            bbox[:2] = kp.get_coords_array()[0]
            bbox[2:4] = kp.get_coords_array()[1]
            (in_grid_H, in_grid_W), yolo_bbox = PASCAL_VOC_bbox_2_yolo(bbox, im_height, im_width, self.GRID_H, self.GRID_W)
            yolo_annotation_array[i, in_grid_H, in_grid_W, 0, 0] = 1
            yolo_annotation_array[i, in_grid_H, in_grid_W, 0, 1: 1+N_classes] = classes_onehot[i]
            yolo_annotation_array[i, in_grid_H, in_grid_W, 0, 1+N_classes:1+N_classes+4] = yolo_bbox
        return yolo_annotation_array
    def __len__(self):
        return int(np.ceil(self.generator.samples / float(self.generator.batch_size)))
    def __getitem__(self, idx):
        data = next(self.generator)
        self.seq_det = self.seq.to_deterministic()
        images_aug = self.seq_det.augment_images(data[0])
        yolo_annot = self.get_yolo_annotations(data[1])
        
        return (images_aug, yolo_annot)
    
    def __next__(self):
        return self.__getitem__(0)
    def __iter__(self):
        return self