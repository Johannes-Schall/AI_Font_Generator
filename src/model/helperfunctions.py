import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
from contextlib import redirect_stdout

def render_charset(charset):
    """
    Renders a charset as a matplotlib figure.

    Args:
        charset (np.array): Array of shape (size, size, num_glyphs)
    """
    num_glyphs = charset.shape[2]
    fig, axs = plt.subplots(1, num_glyphs)
    for idx in range(num_glyphs):
        axs[idx].imshow(charset[:, :, idx], cmap="gray")
        axs[idx].set_xticks([])
        axs[idx].set_yticks([])
    plt.show()

def render_predictions(model, dataset_test, num_examples=4, figsize=(10, 10), 
                       black_white=False, show_plot=True, model_type="3dTensor-3dTensor"):
    """
    Renders the predictions of a model on the test dataset.

    Args:
        model (tf.keras.Model): Model to render the predictions for
        dataset_test (tf.data.Dataset): Test dataset
        num_examples (int, optional): Number of examples to render. Defaults to 4.
        figsize (tuple, optional): Size of the figure. Defaults to (10, 10).
        black_white (bool, optional): Render the predictions in high contrast. Defaults to False.
        show_plot (bool, optional): Show the plot. Defaults to True.

    Returns:
        None if show_plot is True, else (fig, axs)

    """
    if num_examples < 2:
        raise ValueError("num_examples must be at least 2")
    
    if model_type == "3dTensor-3dTensor":
        x_val, y_val = next(iter(dataset_test))
        
        num_glyphs_x = x_val.shape[3]
        num_glyphs_y = y_val.shape[3]

        fig, axs = plt.subplots(num_examples, 
                                num_glyphs_x + num_glyphs_y*2, 
                                figsize=figsize)
        for idx in range(num_examples):
            input_img = x_val[idx, :, :, :]
            target_img = y_val[idx, :, :, :]
            prediction = model.predict(input_img[np.newaxis, :, :, :], verbose=0)
            if black_white:
                #prediction = np.where(prediction > 0.4, 1, 0)
                # increasing the contrast of the prediction with a fermi-dirac function
                temp = 0.05
                prediction = 1 / (1 + np.exp(-(prediction - 0.5)/temp))
            for idx2 in range(num_glyphs_x):
                axs[idx, idx2].imshow(input_img[:, :, idx2], cmap="gray")
                axs[idx, idx2].set_xticks([])
                axs[idx, idx2].set_yticks([])
                axs[idx, idx2].set_title("Input")
            for idx2 in range(num_glyphs_y):
                axs[idx, num_glyphs_x + idx2].imshow(target_img[:, :, idx2], cmap="gray")
                axs[idx, num_glyphs_x + idx2].set_xticks([])
                axs[idx, num_glyphs_x + idx2].set_yticks([])
                axs[idx, num_glyphs_x + idx2].set_title("Target")
            for idx2 in range(num_glyphs_y):
                axs[idx, num_glyphs_x + num_glyphs_y + idx2].imshow(prediction[0, :, :, idx2], cmap="gray")
                axs[idx, num_glyphs_x + num_glyphs_y + idx2].set_xticks([])
                axs[idx, num_glyphs_x + num_glyphs_y + idx2].set_yticks([])
                axs[idx, num_glyphs_x + num_glyphs_y + idx2].set_title("Prediction")
    elif model_type == "2dGrid-OneHot-SingleGlyph":
        for input, target in dataset_test.shuffle(1024).take(1):
            batch_size = input[1].shape[0]
            images_in = input[0]
            one_hot_in = input[1]
            num_predictions_to_plot = num_examples if batch_size > num_examples else batch_size
            prediction = model.predict(input)
            temp = 0.05
            prediction_bw = 1 / (1 + np.exp(-(prediction - 0.5)/temp))
            fig, axs = plt.subplots(num_predictions_to_plot, 4, figsize=(10, 2.5*num_predictions_to_plot))
            for i in range(num_predictions_to_plot):
                axs[i, 0].imshow(images_in[i, :, :], cmap='gray')
                axs[i, 0].set_title("Input")
                axs[i, 0].set_xticks([])
                axs[i, 0].set_yticks([])
                axs[i, 1].imshow(target[i, :, :], cmap='gray')
                axs[i, 1].set_title(f"Target with One Hot:\n{one_hot_in[i]}")
                axs[i, 1].set_xticks([])
                axs[i, 1].set_yticks([])
                axs[i, 2].imshow(prediction[i, :, :], cmap='gray')
                axs[i, 2].set_title("Prediction")
                axs[i, 2].set_xticks([])
                axs[i, 2].set_yticks([])
                axs[i, 3].imshow(prediction_bw[i, :, :], cmap='gray')
                axs[i, 3].set_title("Prediction High Contrast")
                axs[i, 3].set_xticks([])
                axs[i, 3].set_yticks([])
    if show_plot:
        plt.show()
    else:
        return fig, axs

def render_histories(trainings_list, show_plot=True):
    if all(["val_loss" in training["history"].history for training in trainings_list]):
        val_loss_available = True
    else:
        val_loss_available = False

    if len(trainings_list) > 1:
        if val_loss_available:
            fig, axs = plt.subplots(1, 2, figsize=(15, 5))
        else:
            fig, axs = plt.subplots(1, 1, figsize=(5, 5))

        for idx, training in enumerate(trainings_list):
            if val_loss_available:
                axs[0].plot(training["history"].history["loss"], label=f"Training {idx}")
                axs[1].plot(training["history"].history["val_loss"], label=f"Training {idx}")
                axs[0].set_title("Training loss")
                axs[0].set_xlabel("Epoch")
                axs[0].set_ylabel("Loss")
                axs[0].legend()
                axs[1].set_title("Validation loss")
                axs[1].set_xlabel("Epoch")
                axs[1].set_ylabel("Loss")
                axs[1].legend()
            else:
                axs.plot(training["history"].history["loss"], label=f"Training {idx}")
                axs.set_title("Training loss")
                axs.set_xlabel("Epoch")
                axs.set_ylabel("Loss")
                axs.legend()
        
    else:
        fig, axs = plt.subplots(1, 1, figsize=(5, 5))
        axs.plot(trainings_list[0]["history"].history["loss"], label=f"Training Loss")
        if val_loss_available:
            axs.plot(trainings_list[0]["history"].history["val_loss"], label=f"Validation Loss")
            axs.set_title("Training and validation loss")
        else:
            axs.set_title("Training loss")
        axs.set_xlabel("Epoch")
        axs.set_ylabel("Loss")
        axs.legend()

    if show_plot:
        plt.show()
    else:
        return fig, axs

def analyze_trainings(trainings_list):
    # if in the history of the trainings there is a validation loss, we use this for comparison
    if all(["val_loss" in training["history"].history for training in trainings_list]):
        metric_compare = "val_loss"
    else:
        metric_compare = "loss"

    if len(trainings_list) < 2:
        idx_best_training = 0
    else:
        idx_best_training = np.argmin([np.min(training["history"].history[metric_compare]) for training in trainings_list])
        # if this was also the last training
        if idx_best_training == len(trainings_list) - 1:
            print("###############################")
            print("Best training was the last one!")
            print("###############################")
            print("Best training was the last one!")
            print("###############################")
            print("Best training was the last one!")
            print("###############################")
            # getting the index of the second best training
            idx_compare_training = np.argmin([np.min(training["history"].history[metric_compare]) for training in trainings_list[:-1]])
        else:
            idx_compare_training = len(trainings_list) - 1

    print(f"\nThe summary of the model with the best {metric_compare} during training:")
    print(trainings_list[idx_best_training]["history"].model.summary())
    print("\nThe other parameters of the best training:")
    for key, value in trainings_list[idx_best_training].items():
        if key != "history":
            print(f"{key}: {value}")
    # plotting the training and validation loss of the best training and the training to compare
    if "idx_compare_training" in locals():
        render_histories([trainings_list[idx_best_training], trainings_list[idx_compare_training]])
    else:
        render_histories([trainings_list[idx_best_training]])

def save_summary_last_training(trainings_list, dataset_test, save_path_summary, 
                               save_path_model=None, add_prefix="", 
                               model_type="3dTensor-3dTensor"):
    """
    Saves a collection of possible important information about the last training.
    * the model summary
    * the keys and values of the trainings_list (except the history)
    * the plot of the training and validation loss
    * the plot of 10 validation examples with input, target and prediction

    Args:
        trainings_list (list): list of dictionaries with the trainings
        save_path_summary (String): path where the summary files should be saved
        dataset_test (tf.data.Dataset): test dataset
        save_path_model (String, optional): path where the model should be saved. Default None: model is not saved.
    """
    if "val_loss" in trainings_list[-1]["history"].history:
        val_loss_available = True
    else:
        val_loss_available = False
    
    # Prefix for the file names will be the date and time in the format YYYYMMDD_HHMMSS
    prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # add the model type
    prefix += f"_{model_type}"
    # add the prefix from the function arguments
    prefix += f"_{add_prefix}"
    # and addionally the best validation loss and training loss during the last training
    if val_loss_available:
        prefix += f"_val_loss_{np.min(trainings_list[-1]['history'].history['val_loss']):.4f}_train_loss_{np.min(trainings_list[-1]['history'].history['loss']):.4f}"
    else:
        prefix += f"_train_loss_{np.min(trainings_list[-1]['history'].history['loss']):.4f}"

    if not os.path.exists(save_path_summary):
        os.makedirs(save_path_summary)

    # Saving the model summary and the other parameters of the last training
    with open(os.path.join(save_path_summary, f"{prefix}_summary.txt"), "a") as f:
        with redirect_stdout(f):
            trainings_list[-1]["history"].model.summary()
        f.write("\n")
        for key, value in trainings_list[-1].items():
            if key != "history":
                f.write(f"{key}: {value}\n")
        # addionally the lists of the training and validation loss
        f.write(f"training_loss: {trainings_list[-1]['history'].history['loss']}\n")
        if val_loss_available:
            f.write(f"validation_loss: {trainings_list[-1]['history'].history['val_loss']}\n")

    # Saving the plot of the training and validation loss
    fig, axs = render_histories([trainings_list[-1]], show_plot=False)
    fig.savefig(os.path.join(save_path_summary, f"{prefix}_loss.png"), dpi=300)

    # Saving the plot of 10 validation examples with input, target and prediction
    fig, axs = render_predictions(trainings_list[-1]["history"].model, dataset_test, num_examples=10, figsize=(20, 20), show_plot=False, model_type=model_type)
    fig.savefig(os.path.join(save_path_summary, f"{prefix}_predictions.png"), dpi=300)
    fig, axs = render_predictions(trainings_list[-1]["history"].model, dataset_test, num_examples=10, figsize=(20, 20), black_white=True, show_plot=False, model_type=model_type)
    fig.savefig(os.path.join(save_path_summary, f"{prefix}_predictions_black_white.png"), dpi=300)
    #elif model_type == "2dGrid-OneHot-SingleGlyph":


    if save_path_model is not None:
        if not os.path.exists(save_path_model):
            os.makedirs(save_path_model)
        trainings_list[-1]["history"].model.save(os.path.join(save_path_model, f"{prefix}_model.keras"))
        