# <center> AI Font Generator</center>

## Scope

We created the AI Font Generator as part of our final project of DSR Berlin using Python scripts and Jupyter Notebooks.

Background: Creating fonts is a tedious task, usually done by hand. Designers therefore often take shortcuts leaving out glyphs not deemed necessary. That leads to incomplete font sets missing special characters. In our project we are applying machine learning techniques to generate missing special characters necessary in the Germany language like ä, ö, ü, and ß ("Umlaute") that are commonly missing in - primarily English - font sets. Our goal is to have the machine generate those fonts matching the original layout of the font set. This will provide tremendous value to designers outside of the English word space by expanding the range of usable sets.

Our model is created with the idea to allow further expansion, i.e. to add further functionality enabling the model to generate novel font sets from scratch.

## The data

We are using a dataset of approximately 50k font sets. For training, we collected the data making sure that the font sets used are free to use, free of royalty free and the designers allow the usage of their fonts in our project. However, we are no lawyers and given the  time for our project and volume of data, we could not double-check every single font set's license (if it even existed). Hence, we decided to not include the dataset in this repo. However, the notbooks to collect the data are on this repo, just the data and links to the data is missing. We are confident that our work will still provide value to whoever is interested.

#### Data Handling

The font sets get downloaded to a data directory (not on this repo) using the Notebook collecting_all_fonts.ipynb in the notebooks folder. After downloading, the fonts get unzipped and filtered. Our filters check for corrupted files, glyphs that are out of box or missing (either by not having a cmap value or cmap equalling to None).

To detect glyphs that exist but do not have the proper value, i.e. designers put placeholders into the respective slots, we are using OpenAI's CLIP to detect and filter those placeholders.


#### Data Processing

All information about the fonts are stored in a central json file that is being generated at download and further enriched through the filters. It is this central json file that holds all the information and that is further used to access the fonts

## The model

We explored several techniques on how to generate the missing glyphs and decided to focus and compared their results. Our models were trained on the dataset described above. Our goal was to determine the best model for our task. We decided to proceed using a model based on EfficientNet and an Encoder/Decoder model we created from scratch. 
To assess the models' performance, we also compared different techniques, best described as "some chars in, one char out" vs. "many chars in, many chars out". The latter proved to be more efficient with lower loss right off the bat.

#### Assessment

Both models are capable of generating the missing glyphs. The character 'ß' proved to be more challenging than the others and the effects of using CLIP to filter placeholders improved the predictions significantly.

The model we built from scratch turned out to be a notch better than the one built on top of EfficientNet. The generated fonts are more in the same style of the input.

__________

### Folders

Notebooks: Holds the Jupyter notebooks for downloading, filtering and exploring the dataset and notebooks with tests and helpers (like sync_data) we used to synchronize our local datasets.

Src:
- data: Holds the python scripts executed from the notebooks for downloading, filtering, running CLIP classifier, building and handling the central json file. Please note that for running CLIP, a huggingface API Key is required in the local env
- app: For Gradio, the app we created to showcase the generation of glyphs
- model: helperfunctions to run the models

Models: The models we created and logs to assess their validation and training losses


