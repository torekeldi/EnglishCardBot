import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


Base = declarative_base()


class BotUser(Base):

    """Таблица для хранения пользователей бота"""

    __tablename__ = 'bot_user'

    id = sa.Column(sa.Integer, primary_key=True)
    chat_id = sa.Column(sa.Integer, unique=True, nullable=False)


class Word(Base):

    """Таблица для хранения общих и личных слов пользователей"""

    __tablename__ = 'word'

    id = sa.Column(sa.Integer, primary_key=True)
    en_word = sa.Column(sa.String(length=200), nullable=False)
    ru_word = sa.Column(sa.String(length=200), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('bot_user.id'), nullable=True)
    __table_args__ = (sa.UniqueConstraint('en_word', 'user_id', name='uc_user_en_word'), )

    bot_user = relationship(BotUser, backref='word')


class DelWord(Base):

    """Таблица для хранения удаленных слов для каждого пользователя"""

    __tablename__ = 'del_word'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('bot_user.id'), nullable=False)
    word_id = sa.Column(sa.Integer, sa.ForeignKey('word.id'), nullable=False)
    __table_args__ = (sa.UniqueConstraint('user_id', 'word_id', name='uc_del_word_user'),)

    bot_user = relationship(BotUser, backref='del_word')
    word = relationship(Word, backref='del_word')


def create_tables(engine):

    """Функция для очистки базы и создания нужных таблиц"""

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def create_session(engine):

    """Функция создания сессии для работы с базой данных"""

    session = sessionmaker(bind=engine)
    return session()


def create_engine(dsn):

    """Функция создания движка для работы с базой данных"""

    return sa.create_engine(dsn)
