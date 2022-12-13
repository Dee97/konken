from rest_framework.parsers import BaseParser

from urllib.parse import urlparse, parse_qsl, parse_qs

class PlainTextParser(BaseParser):
    """
        Plain text parser
        This allows the body of the received request to be parsed as plain text as opposed to the default JSON.
        NOTE: No longer used
    """
    media_type = 'text/plain'
    charset = 'SHIFT_JIS'

    def parse(self, stream, media_type = None, parse_context = None):
        """
            Returns a dictionary of parameter names and values given a string;
            Ex. 
                > cid=PZ010ABC&typ=00&tim=2020062232148&sts=02
                will be returned as
                data = {
                    "cid": ['PZ010ABC'],
                    "typ": ['00'],
                    "tim":['2020062232148'],
                    "sts": ['02']
                }

                data["cid"][0] will yield 'PZ010ABC'

        """
        text = stream.read().decode('SHIFT_JIS')
        return parse_qs(text)