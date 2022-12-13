from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
import datetime, logging
from django.utils import timezone

logger = logging.getLogger('general')
def open_session(user_id):
    new_expire_date = timezone.now() + datetime.timedelta(days=5)
    try:
        s = Session.objects.get(session_key = user_id)
        if (s.expire_date > timezone.now()):
            s = SessionStore(session_key=user_id)
            s.save()
            return
        else:
            s.delete()
    except Session.DoesNotExist as e:
        logger.info("Session does not exist. Creating new....")   
    s = Session(session_key = user_id, expire_date=new_expire_date)
    s.save()
