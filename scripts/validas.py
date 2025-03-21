"""Example script to demonstrate how to use the validas module.
"""
import json
import os
import logging

from vericlient.client import Client
from requests.models import Response
from vericlient.validas.client import ValidasClient
from vericlient.validas.models import DocumentValidationInput, SelfieInput


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = ValidasClient()
try:

    front_path = "tests/validas/Resources/obverse-ES_IDCard_2015"
    back_path = "tests/validas/Resources/reverse-ES_IDCard_2015"
    selfie_path = "tests/validas/Resources/foto.jpg"
    video_path = "tests/validas/Resources/video.mp4"
    annotations_path = "tests/validas/Resources/annotations_challenge_videophoto.vtt"

    print("\n=== Ejemplo 1: Validación básica con selfie ===")
    result = client.create_complete_validation(
        front_path=front_path,
        back_path=back_path,
        selfie_path=selfie_path,
        document_type="ES_ID",
        service_mode="validation",
        support_nfc=True,
        antispoofing="False"
    )
    
    validation_data = client.get_validation_data(result['validation_id'])
    print(json.dumps(validation_data.data, indent=2))

    print("\n=== Ejemplo 2: Validación con challenge de video ===")
    result_challenge = client.create_complete_validation_with_challenge(
        front_path=front_path,
        back_path=back_path,
        selfie_path=selfie_path,
        video_path=video_path,
        annotations_path=annotations_path,
        document_type="ES_ID",
        service_mode="validation",
        support_nfc=True,
        challenge_length=6,
        challenge_expiration=300  # 5 minutos
    )

    if result_challenge['validation_data']:
        print("\nDatos completos de la validación:")
        print(json.dumps(result_challenge['validation_data'], indent=2))

except Exception as e:
    logger.exception("Error durante el proceso")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        try:
            error_details = e.response.json()
            print(f"Error Details: {json.dumps(error_details, indent=2)}")
        except json.JSONDecodeError:
            if hasattr(e.response, 'text'):
                print(f"Raw Response: {e.response.text}")
            else:
                print("No response text available")
    else:
        print(f"Error sin respuesta HTTP: {str(e)}")
