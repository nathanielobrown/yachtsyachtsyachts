from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

import model


class DataAccessLayer(object):
    def __init__(self, connection_str=None):
        self.connection_str = connection_str
        self.engine = None
        self.Session = None
        self.echo = False

    def connect(self):
        self.engine = create_engine(self.connection_str, echo=self.echo)
        self.Session = sessionmaker(bind=self.engine)
        self.ScopedSession = scoped_session(self.Session)
        self.session = self.ScopedSession()
        return self.session

    def erase_database(self):
        model.Base.metadata.reflect(bind=self.engine)
        model.Base.metadata.drop_all(bind=self.engine)
        model.Base.metadata.create_all(bind=self.engine)
