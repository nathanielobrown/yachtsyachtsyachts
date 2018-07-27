import datetime
from collections import OrderedDict

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class DictMixin(object):
    def __iter__(self):
        for key in list(self.__mapper__.c.keys()):
            yield (key, getattr(self, key))

    def _asdict(self):
        result = OrderedDict()
        for key in list(self.__mapper__.c.keys()):
            result[key] = getattr(self, key)
        return result

    def to_dict(self):
        return self._asdict()


class Search(Base, DictMixin):
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True)
    search_time = Column(DateTime, default=datetime.datetime.now, nullable=False)
    scraper_name = Column(String, nullable=False)
    site_domain = Column(String, nullable=False)
    kwargs = Column(JSON, nullable=False)

    results = relationship("SearchResult")


# class Boat(Base, DictMixin):
#     __tablename__ = 'boats'

#     id = Column(Integer, primary_key=True)


class SearchResult(Base, DictMixin):
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True)
    search_time = Column(DateTime, default=datetime.datetime.now, nullable=False)
    html = Column(String, nullable=False)
    parsed_results = Column(JSON)
    hash = Column(String)

    search_id = Column(ForeignKey("searches.id"), nullable=False)

    search = relationship("Search")


if __name__ == "__main__":
    engine = create_engine(
        "postgresql+psycopg2://postgres@localhost:5433", isolation_level="AUTOCOMMIT"
    )
    Base.metadata.reflect(bind=engine)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    s = Search(site_domain="www.boats.com", args=("contessa", 32), kwargs={})
    r = SearchResult(html="<h1>NOB</h1>", parsed_results={"title": "NOB"})
    s.results.append(r)
    session.add(s)
    session.commit()
