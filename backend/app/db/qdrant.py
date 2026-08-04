import os
import uuid

from dotenv import load_dotenv

from qdrant_client import QdrantClient

from qdrant_client.models import (

    VectorParams,

    Distance,

    PointStruct,

    Filter,

    FieldCondition,

    MatchValue,

    PayloadSchemaType

)

POINT_ID_NAMESPACE = uuid.UUID("a3f1c2d4-0000-4000-8000-000000000000")


load_dotenv()


QDRANT_HOST = os.getenv(
    "QDRANT_HOST"
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY"
)

COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "documents"
)


qdrant_client = QdrantClient(

    url=QDRANT_HOST,

    api_key=QDRANT_API_KEY,

    timeout=60

)


def create_collection():

    collections = qdrant_client.get_collections()

    collection_names = [

        collection.name

        for collection

        in collections.collections

    ]


    if COLLECTION_NAME not in collection_names:

        qdrant_client.create_collection(

            collection_name=

            COLLECTION_NAME,

            vectors_config=

            VectorParams(

                size=768,

                distance=

                Distance.COSINE

            )

        )

        print(

            f"{COLLECTION_NAME} created"

        )

    else:

        print(

            f"{COLLECTION_NAME} already exists"

        )

    qdrant_client.create_payload_index(

        collection_name=COLLECTION_NAME,

        field_name="document_id",

        field_schema=PayloadSchemaType.INTEGER

    )



def similarity_search(

    vector,

    document_id=None,

    limit=5

):

    query_filter = None

    if document_id is not None:

        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )

    response = qdrant_client.query_points(

        collection_name=

        COLLECTION_NAME,

        query=

        vector,

        query_filter=

        query_filter,

        limit=

        limit

    )

    return response.points


def make_point_id(document_id, chunk_index):

    return str(
        uuid.uuid5(
            POINT_ID_NAMESPACE,
            f"{document_id}_{chunk_index}"
        )
    )


def upsert_points(points):

    qdrant_client.upsert(

        collection_name=

        COLLECTION_NAME,

        points=

        points

    )


def delete_points_by_document(document_id):

    qdrant_client.delete(

        collection_name=COLLECTION_NAME,

        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )

    )



def delete_collection():

    qdrant_client.delete_collection(

        collection_name=

        COLLECTION_NAME

    )

    print(

        "Collection deleted"

    )