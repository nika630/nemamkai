#!/usr/bin/env python
import os
from flask_script import Manager, Server
from flask import current_app
from flask_collect import Collect
from app import create_app


class Config(object):
    COLLECT_STATIC_ROOT = os.path.dirname(__file__) + '/static'
    COLLECT_STORAGE = 'flask_collect.storage.file'


app = create_app(Config)

manager = Manager(app)
manager.add_command('runserver', Server(host='127.0.0.1', port=5000))

collect = Collect()
collect.init_app(app)


@manager.command
def collect():
    return current_app.extensions['collect'].collect()


if __name__ == "__main__":
    manager.run()
