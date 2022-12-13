from calendar import timegm
from datetime import datetime
import uuid
from rest_framework_jwt.settings import api_settings


def jwt_payload_handler(user):
    """
        Overrides the default contents of the payload that is going to be encoded.
        To be used when generating JWT tokens from the bot

        Args:   
                user(User): User instance whose details are to be encoded
        
        Returns:
                payload(String): the encoded payload
    """
    payload = {
        'user_id': user.pk,
        'group': user.groups.all()[0].name,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }
    if isinstance(user.pk, uuid.UUID):
        payload['user_id'] = str(user.pk)

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload