#!/usr/bin/env python
import click
import keyring

from task_manager import TaskManager

@click.group()
def main():
    pass

@main.command(help='Download files from CourseNavi')
@click.option('-a', '--all', is_flag=True,
              help='Download every file, not just the ones that are new')
@click.option('-v', '--verbose', is_flag=True,
              help='Print more status logs')
@click.option('-d', '--debug', is_flag=True,
              help='Print status logs for debugging')
def pull(all, verbose, debug):
    tm = TaskManager(all=all, verbose=verbose, debug=debug)
    tm.pull()


@main.command(help='Set your CourseNavi credentials')
@click.option('--email', prompt=True,
              help='Your CourseNavi email address')
@click.option('--password', prompt=True, hide_input=True,
              help='Your CourseNavi password')
def config(email, password):
    keyring.set_password('cnavi-cli', email, password)
    print(f'CourseNavi email and password updated.')


if __name__ == '__main__':
    main()

