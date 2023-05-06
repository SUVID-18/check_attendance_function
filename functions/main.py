from firebase_admin import initialize_app, firestore
from firebase_functions import https_fn, firestore_fn
from google.cloud.firestore import Client

initialize_app()


@https_fn.on_request()
def add(request: https_fn.Request) -> https_fn.Response:
    client: Client = firestore.client()
    (_, document_ref) = client.collection('messages').add({'data': request.args['data']})
    return https_fn.Response(f'{document_ref.id} added.')


@firestore_fn.on_document_created(document='messages/{documentId}')
def auto_upper(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
    print(f'Uppercasing at {event.params["documentId"]}')
    original: str = event.data.get('data')
    event.data.reference.set({'data': original.upper()})
