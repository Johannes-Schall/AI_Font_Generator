""" Classifier to evaluate images with CLIP """

import warnings
import os
import json
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np

from tqdm import tqdm
from . import datarenderer
from . import global_consts as g


# Hugging Face API Key from environment variable
api_key = os.getenv("HUGGING_FACE_API_KEY")

# Load model and processor
model = CLIPModel.from_pretrained(
    "openai/clip-vit-large-patch14", token=api_key)
processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-large-patch14", token=api_key)


def evaluate_image(image_paths, char, text_query=None, verbose=False) -> dict:
    """ Evaluate images

    Args:
        image_path (List[String]): List of image paths
        text_query (List[String]): List of text queries, first category is
            the one to be evaluated

    Returns:
        Dictionary: Returns True if the image is classified as the first category
            in text_query, False otherwise
    """
    results = {}
    warnings.filterwarnings('ignore', message='text_config_dict is provided*')

    # Load the text queries
    if text_query is None:
        with open(g.PATH_TO_QUERIES_JSON, 'r', encoding='utf-8') as file:
            queries_dict = json.load(file)
        text_query = queries_dict[char]

    # Load the images into a numpy array
    # The numpy array will have the shape ([img_data], size, size, [char]])
    print('Rendering images...')
    image_arrays = datarenderer.render_fonts(image_paths, chars=char)

    # Convert images to PIL images
    # CLIP expects RGB and 224x224 images, so we convert the grayscale images to RGB
    # images = [Image.fromarray(np.uint8(img), mode='L').convert(
    #    'RGB').resize((224, 224)) for img in image_arrays[:,:,:,0]]

    # For testing: Not converting to RGB and resizing also works
    images = [Image.fromarray(np.uint8(img), mode='L')
              for img in image_arrays[:, :, :, 0]]

    batch_size = 16

    for i in tqdm(range(0, len(images), batch_size)):
        start_index = i
        end_index = min(i + batch_size, len(images))
        batch_images = images[start_index:end_index]
        inputs = processor(text=text_query,
                           images=batch_images,
                           return_tensors="pt",
                           padding=True)
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1).detach().numpy()

        # print(type(probs))
        # print(probs.shape)
        # print(probs)

        for j, probset in enumerate(probs):
            global_index = i + j
            #print(f"Prob: {probset}")
            if verbose:
                # For testing, print the probabilities
                print(f"Classification for {image_paths[global_index]}:")

                for s, text in enumerate(text_query):
                    print(f"   {text}: {probset[s]:.4f}")

            # Check whether highest score is for first category
            # highest_score_index = np.argmax(probset)
            # print(f"Highest score index: {highest_score_index}")
            # is_first_category = text_query[highest_score_index] == text_query[0]
            results[image_paths[global_index]] = {char: bool(np.argmax(probset) == 0)}

    if verbose:
        print(f'Classification dictionary: {results}')

    return results
