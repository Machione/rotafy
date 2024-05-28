import clicksend_client
import datetime
from jinja2 import Environment, BaseLoader
from rotafy.config import person, chore


class Notifier:
    def __init__(self, clicksend_username: str, clicksend_api_key: str) -> None:
        clicksend_config = clicksend_client.Configuration()
        clicksend_config.username = clicksend_username
        clicksend_config.password = clicksend_api_key
        configured_client = clicksend_client.ApiClient(clicksend_config)
        self.clicksend_api = clicksend_client.SMSApi(configured_client)
        
        self.queue = []
    
    def _ordinal(self, n: int) -> str:
        return f"{n:d}{'tsnrhtdd'[(n//10%10!=1)*(n%10<4)*n%10::4]}"
    
    def format_upcoming_date(self, date: datetime.date) -> str:
        date_ordinal = self._ordinal(date.day)
        
        today = datetime.datetime.today().date()
        days_to_date = (date - today).days
        if days_to_date < 7:
            day_of_week = date.strftime("%A")
            return f"{day_of_week} ({date_ordinal})"
        
        return date.strftime(f"%a {date_ordinal} %b")
    
    def add_to_queue(
            self, 
            message_template: str,
            recipient: person.Person,
            date: datetime.date,
            chore: chore.Chore,
            assignment: str
        ) -> None:
        
        assignment = assignment.replace(recipient.name, "you")
        
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
        self.queue.append(sms)
    
    def send(self) -> None:
        messages_to_send = clicksend_client.SmsMessageCollection(
            messages=[self.queue]
        )
        self.clicksend_api.sms_send_post(messages_to_send)
