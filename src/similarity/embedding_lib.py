import numpy as np
import openai
import yaml

with open("./.secrets.yaml", "r") as f:
    secrets = yaml.safe_load(f)

client = openai.Client(api_key=secrets["OPENAI_API_KEY"])


def get_embedding(text):
    embedding_model = "text-embedding-3-large"
    response = client.embeddings.create(input=text, model=embedding_model)
    return response.data[0].embedding


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def find_k_nearest(data, row_index, k):
    row = data.iloc[row_index]
    embedding = row["embedding_without_assertion"]
    method_name = row["method_name"]

    similarities = data[data["method_name"] != method_name]["embedding"].apply(
        lambda x: cosine_similarity(x, embedding)
    )
    nearest_indices = similarities.nlargest(k)
    nearest_methods = data.iloc[nearest_indices.index]["method"]

    result = []
    for i in nearest_methods.index:
        result.append(nearest_methods[i])
