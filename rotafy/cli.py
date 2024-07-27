import click
import logging
from rotafy.api import manager


@click.group()
@click.argument(
    "configuration_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Print verbose log messages."
)
@click.pass_context
def cli(ctx, configuration_file, verbose):
    log_format = "%(levelname)s @ %(asctime)s - %(message)s"
    log_level = logging.ERROR
    if verbose:
        log_level = logging.INFO

    logging.basicConfig(format=log_format, level=log_level)

    ctx.obj = manager.Manager(configuration_file)


@cli.command("print", help="Print the upcoming rota to the screen.")
@click.pass_obj
def print_to_screen(m):
    m.print()


@cli.command(help="Output the upcoming rota to a PDF file.")
@click.argument("filename", type=click.Path(exists=False), required=True)
@click.pass_obj
def to_pdf(m, filename):
    m.to_pdf(filename)


@cli.command(help="Send notifications to individuals with upcoming chores.")
@click.pass_obj
def notify(m):
    m.notify()


@cli.command(help="Assign a person to a chore on a given date.")
@click.argument("date", type=click.DateTime(), required=True)
@click.argument("chore", type=click.STRING, required=True)
@click.argument("person", type=click.STRING, required=True)
@click.pass_obj
def assign(m, date, chore, person):
    m.add_person(date.date(), chore, person)


@cli.command(help="Swap two peoples' assigned chores on the same date.")
@click.argument("date", type=click.DateTime(), required=True)
@click.argument("person1", type=click.STRING, required=True)
@click.argument("person2", type=click.STRING, required=True)
@click.pass_obj
def swap(m, date, person1, person2):
    m.swap(date.date(), person1, person2)


@cli.command(help="Replace a person with another on a given date.")
@click.argument("date", type=click.DateTime(), required=True)
@click.argument("person", type=click.STRING, required=True)
@click.argument("replacement", type=click.STRING, required=True)
@click.pass_obj
def replace(m, date, person, replacement):
    m.replace(date.date(), person, replacement)


if __name__ == "__main__":
    cli()
