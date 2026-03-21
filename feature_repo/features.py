from datetime import timedelta

from feast import Entity, FeatureView, Field
from feast.types import Float32

user = Entity(name="user_id", join_keys=["user_id"])

user_features = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="ctr", dtype=Float32),
        Field(name="cvr", dtype=Float32),
    ],
    online=True,
)
