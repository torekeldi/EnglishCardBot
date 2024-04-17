from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import select, union_all
import random
from telebot.handler_backends import State, StatesGroup
from translate import Translator


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
engine = sa.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()

token = '7071798660:AAHrL4J72sDLzQn_BV32YDLoA9HGSyXEQg8'
state_storage = StateMemoryStorage()
bot = TeleBot(token, state_storage=state_storage)

buttons = []
shown_words = {}


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово ❌'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    en_word = State()
    ru_word = State()
    ad_word = State()


def show_target(data):
    return f"{data['en_word']} -> {data['ru_word']}"


def show_hint(*lines):
    return '\n'.join(lines)


def get_user_id(cid):
    q = select(BotUser).select_from(BotUser).where(BotUser.chat_id == cid)
    r = session.execute(q).scalar()
    if r:
        result = r.id
    else:
        result = None
    return result


def get_word_id(word, user_id):
    u = union_all(
        select(Word).select_from(Word).where(Word.en_word == word, Word.user_id == user_id),
        select(Word).select_from(Word).where(Word.en_word == word, Word.user_id == None)
    )
    q = select(Word).from_statement(u)
    r = session.execute(q).scalar()
    if r:
        result = r.id
    else:
        result = None
    return result


def add_new_word(message):
    cid = message.chat.id
    uid = get_user_id(cid)
    en_word = message.text.lower().strip()
    if not en_word.isalpha():
        r = 'Слово должно включать только буквы и без пробелов, попробуйте еще раз добавить слово'
        bot.send_message(message.chat.id, r)
    else:
        if get_word_id(en_word, uid):
            r = 'Слово уже есть в базе, попробуйте добавить другое слово'
            bot.send_message(message.chat.id, r)
        else:
            try:
                ts = Translator(to_lang="Russian")
                ru_word = ''.join(x for x in ts.translate(en_word) if x.isalpha()).lower()
                word = Word(en_word=en_word, ru_word=ru_word, user_id=uid)
                session.add(word)
                session.commit()
                all_my_words = get_all_my_words(cid)
                my_words_count = len(list(set(all_my_words[0]).difference(set(all_my_words[1]))))
                r = (f'Слово {en_word} добавлена в базу с переводом {ru_word}.'
                     f'\nВы изучаете {my_words_count} слов. Отлично!❤')
                bot.send_message(message.chat.id, r)
            except:
                r = 'Нет перевода для этого слова, попробуйте добавить другое слово'
                bot.send_message(message.chat.id, r)


def get_all_my_words(cid):
    my_words = []
    del_words = []
    uid = get_user_id(cid)
    u = union_all(
        select(Word).select_from(Word).where(Word.user_id == uid),
        select(Word).select_from(Word).where(Word.user_id == None)
    )
    q1 = select(Word).from_statement(u)
    for obj in session.execute(q1).scalars():
        my_words.append(obj.id)

    q2 = select(DelWord).select_from(DelWord).where(DelWord.user_id == uid)
    for obj in session.execute(q2).scalars():
        del_words.append(obj.word_id)
    return [my_words, del_words]


def choose_words(cid):
    other_words = []
    global shown_words

    all_my_words = get_all_my_words(cid)
    unshown_words1 = list(set(all_my_words[0]).difference(set(all_my_words[1])))
    unshown_words2 = list(set(all_my_words[0]).difference(set(all_my_words[1])).difference(set(shown_words.get(cid))))
    if not unshown_words1:
        chosen_word_id = None
    elif unshown_words1 and not unshown_words2:
        chosen_word_id = random.choice(unshown_words1)
        shown_words[cid] = [chosen_word_id]
    else:
        chosen_word_id = random.choice(unshown_words2)
        add_id = shown_words.get(cid)
        add_id.append(chosen_word_id)
        shown_words[cid] = add_id

    if chosen_word_id:
        q3 = select(Word).select_from(Word).where(Word.id == chosen_word_id)
        r = session.execute(q3).scalar()
        chosen_word_en = r.en_word
        chosen_word_ru = r.ru_word

        q4 = select(Word).select_from(Word).where(Word.en_word != chosen_word_en)
        for obj in session.execute(q4).scalars():
            other_words.append(obj.en_word)
        ad_words = random.sample(other_words, 3)
        result = [chosen_word_id, chosen_word_en, chosen_word_ru, ad_words]
    else:
        result = []

    return result


welcome_message = (
    'Привет 👋\n\nДавай попрактикуемся в английском языке. Тренировки можешь проходить в удобном для себя темпе.'
    '\n\nУ тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.'
    ' Для этого воспользуйся инструментами: '
    '\n\nдобавить слово ➕'
    '\n\nудалить слово ❌'
    '\n\nНу что, начнём ⬇️'
)


@bot.message_handler(commands=['start'])
def create_cards(message):
    cid = message.chat.id
    uid = get_user_id(cid)
    global shown_words
    if not shown_words.get(cid):
        shown_words[cid] = []
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if not data:
                bot.send_message(message.chat.id, welcome_message)
                if not uid:
                    user = BotUser(chat_id=cid)
                    session.add(user)
                    session.commit()
                    bot.send_message(message.chat.id, 'Вы были занесены в базу пользователей бота')
                else:
                    bot.send_message(message.chat.id, 'С возвращением')
    except:
        pass
    markup = types.ReplyKeyboardMarkup(row_width=2)
    global buttons
    buttons = []
    chosen_words = choose_words(cid)
    if chosen_words:
        en_word = chosen_words[1]  # брать из БД
        ru_word = chosen_words[2]  # брать из БД
        en_btn = types.KeyboardButton(en_word)
        buttons.append(en_btn)
        ad_word = chosen_words[3]  # брать из БД
        ad_btn = [types.KeyboardButton(word) for word in ad_word]
        buttons.extend(ad_btn)
        random.shuffle(buttons)
        nxt_btn = types.KeyboardButton(Command.NEXT)
        add_btn = types.KeyboardButton(Command.ADD_WORD)
        del_btn = types.KeyboardButton(Command.DELETE_WORD)
        buttons.extend([del_btn, add_btn, nxt_btn])

        markup.add(*buttons)

        greeting = f"Выбери перевод слова:\n🇷🇺 {ru_word}"
        bot.send_message(message.chat.id, greeting, reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.en_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['en_word'] = en_word
            data['ru_word'] = ru_word
            data['ad_word'] = ad_word
    else:
        bot.send_message(message.chat.id, 'У вас не осталось слов, добавьте новые слова')


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    uid = get_user_id(cid)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if data:
            en_word = data['en_word']
            word_id = get_word_id(en_word, uid)
            q = select(DelWord).select_from(DelWord).where(DelWord.user_id == uid, DelWord.word_id == word_id)
            r = session.execute(q).scalar()
            if r:
                bot.send_message(message.chat.id, f'Слово {en_word} уже есть в списке удаленных слов')
            else:
                del_word = DelWord(user_id=uid, word_id=word_id)
                session.add(del_word)
                session.commit()
                bot.send_message(message.chat.id, f'Слово {en_word} было удалено из вашего списка слов')
        else:
            bot.send_message(message.chat.id, 'Нечего удалять')


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    send = bot.send_message(message.chat.id, 'Введите одно слово на английском')
    bot.register_next_step_handler(send, add_new_word)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        en_word = data['en_word']
        if text == en_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)
        else:
            hint = show_hint("Допущена ошибка!, " f"Попробуй ещё раз вспомнить слово 🇷🇺{data['ru_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
