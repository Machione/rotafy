import clicksend_client
import datetime
from jinja2 import Environment, BaseLoader
from rotafy.config import person, chore


class Notifier:
    def __init__(self, clicksend_username: str, clicksend_api_key: str) -> None:
        clicksend_config = clicksend_client.Configuration()
        clicksend_config.username = clicksend_username
        clicksend_config.password = clicksend_api_key
        clicksend_client = clicksend_client.ApiClient(clicksend_config)
        self.clicksend_api = clicksend_client.SMSApi(clicksend_client)
        
        self.sms_queue = []
    
    def _ordinal(self, n: int) -> str:
        return f"{n:d}{'tsnrhtdd'[(n//10%10!=1)*(n%10<4)*n%10::4]}"
    
    def format_upcoming_date(self, date: datetime.date) -> str:
        date_ordinal = self._ordinal(date.day)
        
        today = datetime.datetime.today().date()
        days_to_date = (date - today).days
        if days_to_date < 7:
            return f"{date.strftime("%A")} ({date_ordinal})"
        
        return date.strftime(f"%a {date_ordinal} %b")
    
    def queue_message(
            self, 
            message_template: str,
            recipient: person.Person,
            date: datetime.date,
            chore: chore.Chore,
            assignment: str
        ) -> None:
        
        if recipient.name == assignment:
            assignment = "you"
        
        jinja_env = Environment(loader=BaseLoader())
        template = jinja_env.from_string(message_template)
        message = template.render(
            recipient=recipient.name,
            date=self.format_upcoming_date(date),
            chore=chore.name,
            assignment=assignment
        )
        
        print(message)
        
        sms = clicksend_client.SmsMessage(
            source="Rotafy",
            body=message,
            to=recipient.telephone
        )
        self.sms_queue.append(sms)
    
    def send_all(self) -> None:
        sms_messages = clicksend_client.SmsMessageCollection(
            messages=self.sms_queue
        )
        # r = self.clicksend_api.sms_send_post(sms_messages)
