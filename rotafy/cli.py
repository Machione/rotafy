import click
import logging
from rotafy.api import manager


@click.group()
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    default=False, 
    help="Print verbose log messages."
)
def cli(verbose):
    log_format = "%(levelname)s @ %(asctime)s - %(message)s"
    log_level = logging.ERROR
    if verbose:
        log_level = logging.INFO
    
    logging.basicConfig(format=log_format, level=log_level)

    

if __name__ == "__main__":
    cli()