"""Example script to demonstrate how to use the esign module.
"""
import os
from random import randint
from vericlient import EsignClient
from vericlient.esign.models import (
    LibraryDocumentInput,
    SignatureRequestInput,
    SignatureInput,
    SignerInput,
    SecurityOptions
)

# Initialize client with API key
client = EsignClient(apikey="your-api-key")

# Check if the service is alive
print(f"Alive: {client.alive()}")

# Create a library document from a PDF file
with open("/Users/greg/Projects/vericlient/tests/data/esign_example.pdf", "rb") as f:
    pdf_data = f.read()

random_number = randint(0, 1000000)

library_document_input = LibraryDocumentInput(
    name=f"Test Document {random_number}",
    file=pdf_data
)
library_document = client.create_library_document(library_document_input)
print(f"Library document created with ID: {library_document.id}")

# Get the library document to verify
document = client.get_library_document(library_document.id)
print(f"Retrieved document: {document.name}")

# Create a signature request
signer = SignerInput(
    name="Test Signer",
    email="test@example.com",
    order=1,
    role="SIGNER",
    security_options=SecurityOptions(
        auth_method="password",
        password="password"
    )
)

signature_request_input = SignatureRequestInput(
    title="Test Signature Request",
    type="manual",
    signers=[signer],
    library_document_ids=[library_document.id],
    ready=False
)
signature_request = client.create_signature_request(signature_request_input)
print(f"Signature request created with ID: {signature_request.id}")

# Send the signature request
sent_request = client.send_signature_request(signature_request.id)
print(f"Signature request sent with status: {sent_request.status}")

# Get the next signature that needs to be signed
next_signature = client.get_next_signature(signature_request.id)
print(f"Next signature ID: {next_signature.id}")

# Sign the document with a selfie
with open("/Users/greg/Projects/vericlient/tests/data/selfie.png", "rb") as f:
    selfie_data = f.read()

signature_input = SignatureInput(
    name_or_initials="TS",
    selfie=selfie_data
)
signed_signature = client.sign_document(
    signature_request_id=signature_request.id,
    signature_id=next_signature.id,
    signature=signature_input
)
print(f"Document signed with status: {signed_signature.status}")

# Finish the signature process
finished_signature = client.finish_signature(
    signature_request_id=signature_request.id,
)
print(f"Signature finished with status: {finished_signature.status}")

# Get the files from the signature request
files = client.get_signature_request_files(signature_request.id)
print(f"Retrieved {len(files)} bytes of files from the signature request")

# Save the signed document
with open("signed.zip", "wb") as f:
    f.write(files)
print("Saved signed document to signed.zip")