import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


Base = declarative_base()


class BotUser(Base):
    __tablename__ = 'bot_user'

    id = sa.Column(sa.Integer, primary_key=True)
    chat_id = sa.Column(sa.Integer, unique=True, nullable=False)


class Word(Base):
    __tablename__ = 'word'

    id = sa.Column(sa.Integer, primary_key=True)
    en_word = sa.Column(sa.String(length=200), nullable=False)
    ru_word = sa.Column(sa.String(length=200), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('bot_user.id'), nullable=True)
    __table_args__ = (sa.UniqueConstraint('en_word', 'user_id', name='uc_user_en_word'), )

    bot_user = relationship(BotUser, backref='word')


class DelWord(Base):
    __tablename__ = 'del_word'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('bot_user.id'), nullable=False)
    word_id = sa.Column(sa.Integer, sa.ForeignKey('word.id'), nullable=False)
    __table_args__ = (sa.UniqueConstraint('user_id', 'word_id', name='uc_del_word_user'),)

    bot_user = relationship(BotUser, backref='del_word')
    word = relationship(Word, backref='del_word')


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


db_type = input('Введите тип базы данных, например: postgresql\n')
db_login = input('Введите пользователя базы данных\n')
db_pass = input('Введите пароль от пользователя базы данных\n')
db_host = input('Введите хост для подключения к базе данных\n')
db_port = input('Введите порт для подключения к базе данных\n')
db_name = input('Введите название базе данных\n')

if not db_type:
    db_type = 'postgresql'
if not db_login:
    db_login = 'postgres'
if not db_pass:
    db_pass = 'postgres'
if not db_host:
    db_host = 'localhost'
if not db_port:
    db_port = 5432
if not db_name:
    db_name = 'postgres'

DSN = f'{db_type}://{db_login}:{db_pass}@{db_host}:{db_port}/{db_name}'
engine1 = sa.create_engine(DSN)
create_tables(engine1)

Session = sessionmaker(bind=engine1)
session = Session()

base_words = {
    "colonel": "полковник", "tight": "плотный", "taught": "учил", "pickling": "маринование", "maid": "прислуга",
    "slip": "скользить", "intention": "намерение", "bush": "куст", "lamb": "ягненок", "pan": "кастрюля"
}

for k, v in base_words.items():
    word = Word(en_word=k, ru_word=v)
    session.add(word)
    session.commit()
