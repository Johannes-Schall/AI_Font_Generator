""" Classifier to evaluate images with CLIP """

import os
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from tqdm import tqdm

# Hugging Face API Key from environment variable
api_key = os.getenv("HUGGING_FACE_API_KEY")

# Load model and processor
model = CLIPModel.from_pretrained(
    "openai/clip-vit-large-patch14", token=api_key)
processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-large-patch14", token=api_key)


def evaluate_image(image_paths, image_arrays, text_queries, char, verbose=False) -> dict:
    """ Evaluate images

    Args:
        image_path (List[String]): List of image paths
        text_queries (List[String]): List of text queries, first category is
            the one to be evaluated

    Returns:
        Dictionary: Returns True if the image is classified as the first category
            in text_queries, False otherwise
    """
    results = {}

    # Convert images to PIL images
    # CLIP expects RGB and 224x224 images, so we convert the grayscale images to RGB
    #images = [Image.fromarray(np.uint8(img), mode='L').convert(
    #    'RGB').resize((224, 224)) for img in image_arrays]

    # For testing: Not converting to RGB and resizing also works
    images = [Image.fromarray(np.uint8(img), mode='L') for img in image_arrays]

    batch_size = 32

    for i in tqdm(range(0, len(images), batch_size)):
        batch_images = images[i:i + batch_size]
        inputs = processor(text=text_queries,
                           images=batch_images,
                           return_tensors="pt",
                           padding=True)
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1).detach().numpy()

        for j, image_prob in enumerate(probs):
            global_index = i + j
            
            if verbose:
                # For testing, print the probabilities
                print(f"Classification for {image_paths[global_index]}:")

                for s, text_query in enumerate(text_queries):
                    print(f"   {text_query}: {image_prob[s]:.4f}")

            # Check whether highest score is for first category
            highest_score_index = np.argmax(image_prob)
            is_first_category = text_queries[highest_score_index] == text_queries[0]
            results[image_paths[global_index]] = {char: is_first_category}

    return results
