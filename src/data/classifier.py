""" Classifier to evaluate images with CLIP """

import os
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np

# Hugging Face API Key from environment variable
api_key = os.getenv("HUGGING_FACE_API_KEY")

# Load model and processor
model = CLIPModel.from_pretrained(
    "openai/clip-vit-large-patch14", use_auth_token=api_key)
processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-large-patch14", use_auth_token=api_key)


def evaluate_image(image_path, text_queries) -> bool:
    """ Evaluate images

    Args:
        image_path (List[String]): List of image paths
        text_queries (List[String]): List of text queries, first category is
            the one to be evaluated

    Returns:
        bool: Returns True if the image is classified as the first category
            in text_queries, False otherwise
    """

    image = Image.open(image_path)
    inputs = processor(text=text_queries, images=image,
                       return_tensors="pt", padding=True)

    # Run model
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1).detach().numpy()

    # Save highest score
    highest_score_index = np.argmax(probs[0])
    highest_score = probs[0][highest_score_index]
    highest_score_category = text_queries[highest_score_index]

    is_first_category = highest_score_category == text_queries[0]

    print(f"Image: {image_path} -"
          f"evaluation: {is_first_category}."
          f"Highest score: {highest_score:.4f} "
          f"for category '{highest_score_category}'")
    
    return is_first_category


# Test data
image_paths = ["../../data/processed/cliptest/1.jpg",
               "../../data/processed/cliptest/2.jpg",
               "../../data/processed/cliptest/3.jpg",
               "../../data/processed/cliptest/4.jpg",
               "../../data/processed/cliptest/5.jpg",
               "../../data/processed/cliptest/6.jpg",
               "../../data/processed/cliptest/7.jpg",
               "../../data/processed/cliptest/8.jpg",
               "../../data/processed/cliptest/9.jpg",
               "../../data/processed/cliptest/10.jpg"]

text_queries = ["letter ß", "letters ss",
                "black box", "rectangle", "not letter ß"]

# Run everything
for image_path in image_paths:
    evaluate_image(image_path, text_queries)
