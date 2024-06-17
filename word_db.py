from db_module import create_tables, Word, create_engine, create_session

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
engine = create_engine(DSN)
create_tables(engine)
session = create_session(engine)


base_words = {
    "colonel": "полковник", "tight": "плотный", "taught": "учил", "pickling": "маринование", "maid": "прислуга",
    "slip": "скользить", "intention": "намерение", "bush": "куст", "lamb": "ягненок", "pan": "кастрюля"
}

for k, v in base_words.items():
    word = Word(en_word=k, ru_word=v)
    session.add(word)
    session.commit()
