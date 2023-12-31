import pandas as pd
import numpy as np
from annoy import AnnoyIndex
from deepface import DeepFace
import argparse

FILE_PATHS = {
    "dataframe": {
        "id": "1HFxHX2RkEr7_yVHnA-qk5Lj8CxOWrUda",
        "name": "final_embeddings_clusters.parquet.gzip",
        "path": "preprocessed_files"
    },
    "AnnoyIndex_Saved_File": {
        "id": "14uIgsVAiGolTy3-TGWrUUXqEzJqh3ZMl",
        "name": "CACD2000_refined_images_embeddings_clusters.ann",
            "path": "preprocessed_files"
        }
    }

def download_file(file_id, file_name, save_path):
    """Function to generate the urls for given params"""
    url = r"""wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id={FILE_ID}' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id={FILE_ID}" -O {SAVE_PATH}/{FILE_NAME} && rm -rf /tmp/cookies.txt""".format(
        FILE_ID=file_id, FILE_NAME=file_name, SAVE_PATH=save_path
    )
    os.system(url)


"""
Prepare env for using this file, use this function
if running code without backend.
"""
def download_required_files():
    programs = []
    for key, details in MODEL_PATHS.items():
        if not os.path.exists(details["path"]):
            os.makedirs(details["path"])
            proc = Process(target=download_file, args=(
                    details["id"], details["name"], details["path"],))
            programs.append(proc)
            proc.start()

    for proc in programs:
        proc.join()

    return "Environent Ready!"

def get_similar_images_annoy(t, df, img_index, n=10, max_dist=10):
    vid, face  = df.iloc[img_index, [0, 1]]
    similar_img_ids, dist = t.get_nns_by_item(img_index, n+1, include_distances=True)
    temp = similar_img_ids[::-1]
    dtemp = dist[::-1]
    t1 = []
    for s,d in zip(temp, dtemp):
      t1.append(s)
    similar_img_ids = t1[1:]
    return vid, vid, df.iloc[similar_img_ids], dist

def get_sample_n_similar(t,df,sample_idx):
    output_images = []
    vid, face, similar, distances = get_similar_images_annoy(t, df, sample_idx)
    list_plot = [face] + similar['face'].values.tolist()
    list_cluster = [df.iloc[sample_idx]['cluster']] + similar['cluster'].values.tolist()
    for face, cluster, dist in zip(list_plot, list_cluster, distances):
      try:
        output_images.append(f'{face.split("/")[-1][:-4]}.jpg')
      except:
        continue
    return output_images

def add_to_dataframe(image_path, dataframe):
    embedding_json = {}
    embedding_json['face'] = image_path
    embedding_objs = DeepFace.represent(img_path = image_path)
    embedding_json.update(embedding_objs[0])  
    _ = pd.json_normalize(embedding_json)
    _ = _.drop(columns=["facial_area.x", "facial_area.y", "facial_area.w", "facial_area.h", "embedding"])
    dataframe = pd.concat([_, dataframe], sort=False)
    
    return dataframe

def get_similar_images(image_path):
    df = pd.read_parquet(FILE_PATHS["dataframe"]["path"] + "/" + FILE_PATHS["dataframe"]["name"])
    df = add_to_dataframe(image_path, df)
    f = 2622
    t = AnnoyIndex(2622, metric='euclidean')
    ntree = 5
    for i, vector in enumerate(df['embedding']):
        t.add_item(i, vector)
    _  = t.build(ntree)
    
    results = get_sample_n_similar(t, df, 0)
    del df
    del t

    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.parse_args()
    parser.add_argument("image_file_path", help="Enter the apth of the image file that you need similar images for")
    args = parser.parse_args()
    image_path = str(args.image_file_path)
    get_similar_images(image_path)