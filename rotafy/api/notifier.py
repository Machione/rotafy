import clicksend_client
import logging
import datetime
import jinja2
from rotafy.config import person
from rotafy.rota import assignment, printable


logger = logging.getLogger(__name__)


class Notifier:
    def __init__(
        self, clicksend_username: str, clicksend_api_key: str, message_template: str
    ) -> None:
        clicksend_config = clicksend_client.Configuration()
        clicksend_config.username = clicksend_username
        clicksend_config.password = clicksend_api_key
        configured_client = clicksend_client.ApiClient(clicksend_config)
        self.clicksend_api = clicksend_client.SMSApi(configured_client)

        jinja_env = jinja2.Environment(loader=jinja2.BaseLoader())
        self.template = jinja_env.from_string(message_template)

        self.queue = []

    def format_upcoming_date(self, date: datetime.date) -> str:
        date_ordinal = printable.ordinal(date.day)

        today = datetime.date.today()
        days_to_date = (date - today).days
        if days_to_date < 7:
            day_of_week = date.strftime("%A")
            return f"{day_of_week} ({date_ordinal})"

        return printable.human_readable_date(date, True, False)

    def add_to_queue(
        self, recipient: person.Person, assignment_to_notify: assignment.Assignment
    ) -> None:
        assignment_str = str(assignment_to_notify)
        assignment_msg = assignment_str.replace(recipient.name, "you")

        message = self.template.render(
            recipient=recipient.name,
            date=self.format_upcoming_date(assignment_to_notify.date),
            chore=assignment_to_notify.chore.name,
            assignment=assignment_msg,
        )

        logger.info(f"Adding message '{message}' to {recipient.telephone} to queue")
        sms = clicksend_client.SmsMessage(
            source="Rotafy", body=message, to=recipient.telephone
        )
        self.queue.append(sms)

    def message_from_assignment(
        self, assignment_to_notify: assignment.Assignment
    ) -> None:
        self.add_to_queue(assignment_to_notify.person, assignment_to_notify)
        if assignment_to_notify.trainee is not None:
            self.add_to_queue(assignment_to_notify.trainee, assignment_to_notify)

    def send(self) -> None:
        messages_to_send = clicksend_client.SmsMessageCollection(messages=[self.queue])
        try:
            self.clicksend_api.sms_send_post(messages_to_send)
        except Exception as e:
            raise e
        else:
            logger.info(f"All {len(self.queue)} messages in queue sent")
            self.queue = []
