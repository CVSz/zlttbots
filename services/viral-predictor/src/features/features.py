import numpy as np

def extract_features(video):

    views = video["views"]
    likes = video["likes"]
    comments = video["comments"]
    shares = video["shares"]

    engagement = (likes + comments + shares) / max(views,1)

    return np.array([
        views,
        likes,
        comments,
        shares,
        engagement
    ])
