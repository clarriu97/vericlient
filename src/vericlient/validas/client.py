"""Implementation of the client for the vali-Das service."""
import json
import logging
import os
from typing import Dict, List, Optional, Union

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.exceptions import UnsupportedMediaTypeError
from vericlient.utils import get_virtual_file
from vericlient.validas.endpoints import ValidasEndpoints
from vericlient.validas.exceptions import (
    DocumentError,
    DocumentValidationError,
    EmptyDocumentError,
    InvalidDocumentError,
    DocumentServiceError,
    EmptySelfieError,
    EmptyVideoError,
    EmptyAnnotationsError,
    VideoPhotoChallengeError,
    UnknownChallengeTypeError,
    InvalidTokenError,
    NotAllowedServiceModeError,
    ValidationProcessError
)
from vericlient.validas.models import (
    CreateValidation,
    DocumentValidationInput,
    DocumentValidationOutput,
    SelfieInput,
    SelfieOutput,
    ValidationDataResponse,
    ChallengeInput,
    ChallengeOutput,
    VideoChallengeInput,
    VideoChallengeOutput
)

logger = logging.getLogger(__name__)

class ValidasClient(Client):
    """Class to interact with the vali-Das API."""

    def __init__(
            self,
            apikey: str | None = None,
            timeout: int | None = None,
            environment: str | None = None,
            location: str | None = None,
            url: str | None = None,
            headers: dict | None = None,
    ) -> None:
        """Create the DaspeakClient class.

        Args:
            apikey: The API key to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        api = APIs.VALIDAS.value
        super().__init__(
            api=api,
            apikey=apikey,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )
        # Mapeo de excepciones del servidor a excepciones del cliente
        self._exceptions = {
            "EmptyDocument": EmptyDocumentError,
            "InvalidDocument": InvalidDocumentError,
            "DocumentValidation": DocumentServiceError,
            "EmptySelfie": EmptySelfieError,
            "EmptyVideo": EmptyVideoError,
            "EmptyAnnotations": EmptyAnnotationsError,
            "VideoPhotoChallengeNotAllowed": VideoPhotoChallengeError,
            "UnknownChallengeType": UnknownChallengeTypeError,
            "InvalidToken": InvalidTokenError,
            "NotAllowedServiceMode": NotAllowedServiceModeError,
            "ValidationError": ValidationProcessError
        }

    def _handle_error_response(self, response: Response) -> None:
        """Handle error responses from the API."""
        try:
            response_json = response.json()
            error_type = response_json.get("error_type")
            error_message = response_json.get("error_message", "Unknown error")
            analysis_type = response_json.get("analysis_type")

            if error_type in self._exceptions:
                exception_class = self._exceptions[error_type]
                
                # Casos especiales que necesitan parámetros adicionales
                if error_type == "DocumentValidation":
                    raise exception_class(error_message, analysis_type)
                elif error_type in ["EmptyDocument", "InvalidDocument"]:
                    raise exception_class(analysis_type)
                else:
                    raise exception_class()
            
            self._raise_server_error(response)
        except json.JSONDecodeError:
            self._raise_server_error(response)

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=ValidasEndpoints.ALIVE.value)
        accepted_status_code = 200
        return response.status_code == accepted_status_code
    
    def create_validation(self) -> CreateValidation:
        """Create a new validation process."""
        endpoint = ValidasEndpoints.CREATE_VALIDATION.value
        response = self._post(endpoint=endpoint)
        json_data = response.json()
        # Añadir versión si no existe
        if "version" not in json_data:
            json_data["version"] = "1.0"  # o el valor que corresponda
        return CreateValidation(status_code=response.status_code, **json_data)

    def get_validation_data(self, validation_id: str, accept_format: str = None) -> ValidationDataResponse:
        """Get validation data.
        
        Args:
            validation_id: The ID of the validation
            accept_format: Optional format for the response. Can be 'zip' or 'zip-nojson'
            
        Returns:
            ValidationDataResponse: The validation data
            
        Raises:
            DocumentValidationError: If there's an error getting the validation data
        """
        endpoint = ValidasEndpoints.GET_VALIDATION_DATA.value.replace("<validation_id>", validation_id)
        
        # Prepare headers
        headers = {}
        if accept_format:
            if accept_format not in ['zip', 'zip-nojson']:
                raise ValueError("accept_format must be either 'zip' or 'zip-nojson'")
            headers['Accept'] = accept_format
            
        try:
            response = self._get(endpoint=endpoint, headers=headers)
            
            if response is None:
                raise DocumentValidationError("No response received from server")
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content type: {response.headers.get('Content-Type')}")
            
            # Si la respuesta es un zip, devolver los bytes directamente
            if accept_format and 'zip' in accept_format:
                return ValidationDataResponse(
                    status_code=response.status_code,
                    version="1.0",
                    data={"content": response.content}
                )
            
            # Para respuestas JSON normales
            try:
                json_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response: {response.text}")
                json_data = {"message": "Response format unknown"}
            
            # Añadir versión si no existe
            if "version" not in json_data:
                json_data["version"] = "1.0"
            
            return ValidationDataResponse(
                status_code=response.status_code,
                **json_data
            )
            
        except Exception as e:
            logger.error(f"Error in get_validation_data: {str(e)}")
            raise
    
    def upload_document(
        self, 
        validation_id: str, 
        document: str | bytes,
        analysis_type: str,  # "obverse" o "reverse"
        document_type: str = None,
        service_mode: str = "validation",
        scores_configuration: dict = None,
        support_nfc: bool = None,
        documents_to_process: int = None
    ) -> DocumentValidationOutput:
        """Validate a document in an existing validation process."""
        # Validación de parámetros
        if analysis_type == "obverse" and not document_type:
            raise ValueError("document_type is required when analysis_type is 'obverse'")
        
        endpoint = ValidasEndpoints.VALIDATION_DOCUMENT.value.replace("<validation_id>", validation_id)
        logger.debug(f"Endpoint constructed: {endpoint}")
        
        # Verificar que el documento no está vacío
        if isinstance(document, str) and not os.path.exists(document):
            raise EmptyDocumentError(analysis_type)
        elif isinstance(document, bytes) and not document:
            raise EmptyDocumentError(analysis_type)
        
        # Preparar los archivos para el formulario multipart
        files = {}
        document_file = get_virtual_file(document)
        files["documentImage"] = (f"{analysis_type}.jpg", document_file, "image/jpeg")
        
        # Preparar los datos del formulario
        data = {
            "analysisType": analysis_type,
            "serviceMode": service_mode,
        }
        
        # Añadir el tipo de documento si es necesario
        if document_type:
            data["documentType"] = document_type
        
        # Agregar configuración de puntuaciones si existe y es análisis de anverso
        if scores_configuration and analysis_type == "obverse":
            data["scoresConfiguration"] = json.dumps(scores_configuration)
        
        # Agregar soporte NFC si se especifica
        if support_nfc is not None:
            data["supportNfc"] = str(support_nfc).lower()
        
        # Agregar número de documentos adicionales si se especifica
        if documents_to_process is not None:
            data["documentsToProcess"] = documents_to_process
        
        logger.debug(f"Sending request with data: {data}")
        
        try:
            # Realizar la petición
            response = self._put(endpoint=endpoint, data=data, files=files)
            
            if response is None:
                raise DocumentServiceError("No response received from server", analysis_type)
                
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            # Si la respuesta es exitosa pero no tiene contenido
            if response.status_code == 204:
                return DocumentValidationOutput(
                    status_code=response.status_code,
                    version="1.0",
                    data={"message": f"{analysis_type} document uploaded successfully"}
                )
            
            # Intentar parsear la respuesta JSON
            try:
                json_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response: {response.text}")
                json_data = {"message": f"{analysis_type} document processed but response format unknown"}
            
            if "version" not in json_data:
                json_data["version"] = "1.0"
                
            return DocumentValidationOutput(
                status_code=response.status_code,
                **json_data
            )
            
        except Exception as e:
            logger.error(f"Error in upload_document: {str(e)}")
            raise

    def upload_selfie(self, validation_id: str, data_model: SelfieInput) -> SelfieOutput:
        """Upload a selfie for validation.

        Args:
            validation_id: The ID of the validation
            data_model: The data required for selfie validation

        Returns:
            SelfieOutput: The response from the service

        Raises:
            InvalidInputError: If the provided selfie is invalid
            UnsupportedMediaTypeError: If the media type is not supported
        """
        endpoint = ValidasEndpoints.VALIDATION_SELFIE.value.replace("<validation_id>", validation_id)
        
        # Verificar que la imagen no está vacía
        if isinstance(data_model.image, str) and not os.path.exists(data_model.image):
            raise EmptySelfieError()
        elif isinstance(data_model.image, bytes) and not data_model.image:
            raise EmptySelfieError()
        
        # Preparar los archivos
        image = get_virtual_file(data_model.image) 
        files = {
            "image": ("image.jpg", image, "image/jpeg"),
        }
        
        data = {}
        if data_model.image_alive is not None:
            if isinstance(data_model.image_alive, str) and not os.path.exists(data_model.image_alive):
                raise EmptySelfieError()
            elif isinstance(data_model.image_alive, bytes) and not data_model.image_alive:
                raise EmptySelfieError()
            
            image_alive = get_virtual_file(data_model.image_alive)
            files["image_alive"] = ("image_alive.jpg", image_alive, "image/jpeg")
        
        if data_model.antispoofing is not None:
            data["antispoofing"] = data_model.antispoofing
        
        try:
            response = self._put(endpoint=endpoint, data=data, files=files)
            
            if response is None:
                raise DocumentServiceError("No response received from server")
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            # Si la respuesta es exitosa pero no tiene contenido
            if response.status_code == 204 or not response.text.strip():
                return SelfieOutput(
                    status_code=response.status_code,
                    version="1.0",
                    data={"message": "Selfie uploaded successfully"}
                )
            
            # Intentar parsear la respuesta JSON
            try:
                json_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response: {response.text}")
                return SelfieOutput(
                    status_code=response.status_code,
                    version="1.0",
                    data={"message": "Selfie processed but response format unknown"}
                )
            
            # Añadir versión si no existe
            if "version" not in json_data:
                json_data["version"] = "1.0"
            
            return SelfieOutput(status_code=response.status_code, **json_data)
            
        except Exception as e:
            logger.error(f"Error in upload_selfie: {str(e)}")
            raise

    def generate_challenge(self, validation_id: str, data_model: ChallengeInput) -> ChallengeOutput:
        """Generate a random challenge for the validation process.

        Args:
            validation_id: The ID of the validation
            data_model: The configuration for the challenge generation

        Returns:
            ChallengeOutput: The response from the service containing the challenge data

        Raises:
            DocumentValidationError: If there's an error generating the challenge
        """
        endpoint = ValidasEndpoints.VALIDATION_CHALLENGE.value.replace("<validation_id>", validation_id)
        
        data = {
            "type": data_model.type,
            "length": data_model.length,
            "expiration": data_model.expiration
        }
        
        try:
            response = self._put(endpoint=endpoint, data=data)
            
            if response is None:
                raise DocumentValidationError("No response received from server")
            
            logger.debug(f"Response status code: {response.status_code}")
            
            # Si la respuesta es exitosa pero no tiene contenido
            if response.status_code == 204:
                return ChallengeOutput(
                    status_code=response.status_code,
                    version="1.0",
                    data={"message": "Challenge generated successfully"}
                )
            
            # Intentar parsear la respuesta JSON
            try:
                json_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response: {response.text}")
                json_data = {"message": "Challenge generated but response format unknown"}
            
            # Añadir versión si no existe
            if "version" not in json_data:
                json_data["version"] = "1.0"
            
            return ChallengeOutput(
                status_code=response.status_code,
                **json_data
            )
            
        except Exception as e:
            logger.error(f"Error in generate_challenge: {str(e)}")
            raise

    def upload_video_challenge(self, validation_id: str, data_model: VideoChallengeInput) -> VideoChallengeOutput:
        """Upload a video challenge response.

        Args:
            validation_id: The ID of the validation
            data_model: The data required for video challenge submission

        Returns:
            VideoChallengeOutput: The response from the service

        Raises:
            InvalidInputError: If the provided files are invalid
            UnsupportedMediaTypeError: If the media type is not supported
        """
        endpoint = ValidasEndpoints.VALIDATION_CHALLENGE_VIDEO_PHOTO.value.replace("<validation_id>", validation_id)
        
        # Verificar que los archivos no están vacíos
        for file_attr, file_path, error_class in [
            ("selfie", data_model.selfie, EmptySelfieError),
            ("video", data_model.video, EmptyVideoError),
            ("annotations", data_model.annotations, EmptyAnnotationsError)
        ]:
            if isinstance(file_path, str) and not os.path.exists(file_path):
                raise error_class()
            elif isinstance(file_path, bytes) and not file_path:
                raise error_class()
        
        # Preparar los archivos
        files = {
            "selfie": ("selfie.jpg", get_virtual_file(data_model.selfie), "image/jpeg"),
            "video": ("video.mp4", get_virtual_file(data_model.video), "video/mp4"),
            "annotations": ("annotations.vtt", get_virtual_file(data_model.annotations), "text/vtt"),
        }
        
        # Preparar datos adicionales si existen
        data = {}
        if data_model.videoFrames is not None:
            data["videoFrames"] = json.dumps(data_model.videoFrames)
        if data_model.audio is not None:
            data["audio"] = data_model.audio
        
        try:
            response = self._put(endpoint=endpoint, data=data, files=files)
            
            if response is None:
                raise DocumentServiceError("No response received from server")
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            # Si la respuesta es exitosa pero no tiene contenido
            if response.status_code == 204:
                return VideoChallengeOutput(
                    status_code=response.status_code,
                    version="1.0",
                    data={"message": "Video challenge uploaded successfully"}
                )
            
            # Intentar parsear la respuesta JSON
            try:
                json_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response: {response.text}")
                json_data = {"message": "Video challenge processed but response format unknown"}
            
            # Añadir versión si no existe
            if "version" not in json_data:
                json_data["version"] = "1.0"
            
            return VideoChallengeOutput(
                status_code=response.status_code,
                **json_data
            )
            
        except Exception as e:
            logger.error(f"Error in upload_video_challenge: {str(e)}")
            raise

    def create_complete_validation(
        self,
        front_path: str,
        back_path: str,
        selfie_path: str,
        document_type: str = "ES_ID",
        service_mode: str = "validation",
        support_nfc: bool = True,
        scores_configuration: dict = None,
        antispoofing: str = "False"
    ) -> Dict:
        """Create a complete validation including document uploads and selfie.
        
        Args:
            front_path: Path to the front/obverse document image
            back_path: Path to the back/reverse document image
            selfie_path: Path to the selfie image
            document_type: Type of document (default: "ES_ID")
            service_mode: Service mode (default: "validation")
            support_nfc: Whether to support NFC (default: True)
            scores_configuration: Optional scores configuration for document validation
            antispoofing: Antispoofing setting for selfie (default: "False")
            
        Returns:
            Dict containing:
                - validation_id: The ID of the created validation
                - front_response: Response from front document upload
                - back_response: Response from back document upload
                - selfie_response: Response from selfie upload
                
        Raises:
            FileNotFoundError: If any of the required files don't exist
            DocumentValidationError: If there's an error in any step of the validation
        """
        # Verificar que los archivos existen
        for path, desc in [
            (front_path, "anverso"),
            (back_path, "reverso"),
            (selfie_path, "selfie")
        ]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"No se encuentra el archivo del {desc}: {path}")
        
        logger.debug("Iniciando proceso de validación completa...")
        
        try:
            # 1. Crear nueva validación
            logger.debug("Creando nueva validación...")
            validation_response = self.create_validation()
            validation_id = validation_response.data['id']
            logger.debug(f"Validation ID creado: {validation_id}")
            
            # 2. Subir anverso
            logger.debug("Subiendo anverso...")
            front_result = self.upload_document(
                validation_id=validation_id,
                document=front_path,
                analysis_type="obverse",
                document_type=document_type,
                service_mode=service_mode,
                support_nfc=support_nfc,
                scores_configuration=scores_configuration
            )
            logger.debug(f"Anverso procesado. Status: {front_result.status_code}")
            
            # 3. Subir reverso
            logger.debug("Subiendo reverso...")
            back_result = self.upload_document(
                validation_id=validation_id,
                document=back_path,
                analysis_type="reverse",
                document_type=document_type,
                service_mode=service_mode,
                support_nfc=support_nfc
            )
            logger.debug(f"Reverso procesado. Status: {back_result.status_code}")
            
            # 4. Subir selfie
            logger.debug("Subiendo selfie...")
            selfie_input = SelfieInput(
                image=selfie_path,
                antispoofing=antispoofing
            )
            selfie_result = self.upload_selfie(
                validation_id=validation_id,
                data_model=selfie_input
            )
            logger.debug(f"Selfie procesado. Status: {selfie_result.status_code}")
            
            # 5. Preparar respuesta
            result = {
                "validation_id": validation_id,
                "front_response": front_result.data if hasattr(front_result, "data") else None,
                "back_response": back_result.data if hasattr(back_result, "data") else None,
                "selfie_response": selfie_result.data if hasattr(selfie_result, "data") else None
            }
            
            logger.debug("Proceso de validación completa finalizado exitosamente")
            return result
            
        except Exception as e:
            logger.error(f"Error durante el proceso de validación completa: {str(e)}")
            raise

    def create_complete_validation_with_challenge(
        self,
        front_path: str,
        back_path: str,
        selfie_path: str,
        video_path: str,
        annotations_path: str,
        document_type: str = "ES_ID",
        service_mode: str = "validation",
        support_nfc: bool = True,
        scores_configuration: dict = None,
        challenge_length: int = 6,
        challenge_expiration: int = 300,
        video_frames: dict = None,
        audio: str = None
    ) -> Dict:
        """Create a complete validation including document uploads and video challenge.
        
        Args:
            front_path: Path to the front/obverse document image
            back_path: Path to the back/reverse document image
            selfie_path: Path to the selfie image for the video challenge
            video_path: Path to the video file for the challenge
            annotations_path: Path to the annotations file for the challenge
            document_type: Type of document (default: "ES_ID")
            service_mode: Service mode (default: "validation")
            support_nfc: Whether to support NFC (default: True)
            scores_configuration: Optional scores configuration for document validation
            challenge_length: Length of the challenge code (default: 6)
            challenge_expiration: Challenge expiration time in seconds (default: 300)
            video_frames: Optional video frames data
            audio: Optional audio file path
            
        Returns:
            Dict containing:
                - validation_id: The ID of the created validation
                - front_response: Response from front document upload
                - back_response: Response from back document upload
                - challenge_response: Response from challenge generation
                - video_challenge_response: Response from video challenge upload
                - validation_data: Complete validation data
                
        Raises:
            FileNotFoundError: If any of the required files don't exist
            DocumentValidationError: If there's an error in any step of the validation
        """
        # Verificar que los archivos existen
        for path, desc in [
            (front_path, "anverso"),
            (back_path, "reverso"),
            (selfie_path, "selfie"),
            (video_path, "video"),
            (annotations_path, "anotaciones")
        ]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"No se encuentra el archivo del {desc}: {path}")
        
        logger.debug("Iniciando proceso de validación completa con challenge...")
        
        try:

            logger.debug("Creando nueva validación...")
            validation_response = self.create_validation()
            validation_id = validation_response.data['id']

            logger.debug("Subiendo anverso...")
            front_result = self.upload_document(
                validation_id=validation_id,
                document=front_path,
                analysis_type="obverse",
                document_type=document_type,
                service_mode=service_mode,
                support_nfc=support_nfc,
                scores_configuration=scores_configuration
            )
            logger.debug(f"Anverso procesado. Status: {front_result.status_code}")

            logger.debug("Subiendo reverso...")
            back_result = self.upload_document(
                validation_id=validation_id,
                document=back_path,
                analysis_type="reverse",
                document_type=document_type,
                service_mode=service_mode,
                support_nfc=support_nfc
            )
            logger.debug(f"Reverso procesado. Status: {back_result.status_code}")

            logger.debug("Generando challenge...")
            challenge_input = ChallengeInput(
                type="selfie-alive-pro", 
                length=str(challenge_length),
                expiration=challenge_expiration
            )

            challenge_result = self.generate_challenge(
                validation_id=validation_id,
                data_model=challenge_input
            )
            logger.debug(f"Challenge generado. Status: {challenge_result.status_code}")
            
            logger.debug("Subiendo respuesta del challenge...")
            video_challenge_input = VideoChallengeInput(
                selfie=selfie_path,  # Usamos la imagen de selfie proporcionada
                video=video_path,
                annotations=annotations_path,
                videoFrames=video_frames,
                audio=audio
            )
            video_challenge_result = self.upload_video_challenge(
                validation_id=validation_id,
                data_model=video_challenge_input
            )
            logger.debug(f"Challenge de video procesado. Status: {video_challenge_result.status_code}")
            
            logger.debug("Obteniendo datos completos de la validación...")
            validation_data = self.get_validation_data(validation_id)
            
            result = {
                "validation_id": validation_id,
                "front_response": front_result.data if hasattr(front_result, "data") else None,
                "back_response": back_result.data if hasattr(back_result, "data") else None,
                "challenge_response": challenge_result.data if hasattr(challenge_result, "data") else None,
                "video_challenge_response": video_challenge_result.data if hasattr(video_challenge_result, "data") else None,
                "validation_data": validation_data.data if hasattr(validation_data, "data") else None
            }
            
            logger.debug("Proceso de validación completa con challenge finalizado exitosamente")
            return result
            
        except Exception as e:
            logger.error(f"Error durante el proceso de validación completa con challenge: {str(e)}")
            raise