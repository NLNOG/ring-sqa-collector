"""
This file has been automatically generated with workbench_alchemy v0.2.1
For more details please check here:
https://github.com/PiTiLeZarD/workbench_alchemy
"""

USE_MYSQL_TYPES = True
try:
    from . import USE_MYSQL_TYPES
except:
    pass


from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

if USE_MYSQL_TYPES:
    from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, DATETIME, ENUM, TEXT
else:
    from sqlalchemy import Integer as INTEGER, String as VARCHAR, DateTime as DATETIME, Enum as ENUM, String as TEXT

DECLARATIVE_BASE = declarative_base()


class SqaCorrelator(DECLARATIVE_BASE):

    __tablename__ = 'sqa_correlator'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'sqlite_autoincrement': True, 'mysql_charset': 'utf8'}
    )

    id = Column(INTEGER, autoincrement=True, primary_key=True, nullable=False)  # pylint: disable=invalid-name
    object = Column(VARCHAR(45), nullable=False)
    percentage = Column(INTEGER, nullable=False)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<SqaCorrelator(%(id)s)>" % self.__dict__


class SqaCollector(DECLARATIVE_BASE):

    __tablename__ = 'sqa_collector'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'sqlite_autoincrement': True, 'mysql_charset': 'utf8'}
    )

    id = Column(INTEGER, autoincrement=True, primary_key=True, nullable=False)  # pylint: disable=invalid-name
    started = Column(DATETIME, nullable=False)
    ended = Column(DATETIME)
    raised_by = Column(VARCHAR(45), default='unknown', nullable=False)
    afi = Column(ENUM('ipv4','ipv6'), default='ipv4', nullable=False)
    short = Column(VARCHAR(100))
    long = Column(TEXT(100))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<SqaCollector(%(id)s)>" % self.__dict__


class SqaCollectorCorrelator(DECLARATIVE_BASE):

    __tablename__ = 'sqa_collector_correlator'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'sqlite_autoincrement': True, 'mysql_charset': 'utf8'}
    )

    id = Column(INTEGER, autoincrement=True, primary_key=True, nullable=False)  # pylint: disable=invalid-name
    collector_id = Column(
        INTEGER, ForeignKey("sqa_collector.id", onupdate="CASCADE", ondelete="CASCADE"), index=True, nullable=False
    )
    correlator_id = Column(
        INTEGER, ForeignKey("sqa_correlator.id", onupdate="CASCADE", ondelete="CASCADE"), index=True, nullable=False
    )

    sqaCorrelator = relationship("SqaCorrelator", foreign_keys=[correlator_id], backref="sqaCollectorCorrelator")
    sqaCollector = relationship("SqaCollector", foreign_keys=[collector_id], backref="sqaCollectorCorrelator")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<SqaCollectorCorrelator(%(id)s)>" % self.__dict__

