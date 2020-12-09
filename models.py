import os
from random import randint

import pandas
import psycopg2
from dotenv import load_dotenv
from flask_login import UserMixin
from peewee import *
from playhouse.db_url import connect


load_dotenv()

if 'HEROKU' in os.environ:
    database = connect(os.environ.get('DATABASE_URL'))
else:
    DATABASE = os.getenv('DATABASE')
    USER = os.getenv('USER')
    PASSWORD = os.getenv('PASSWORD')
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    database = PostgresqlDatabase(
        DATABASE,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
    )


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class Difficulty(BaseModel):
    difficulty_id = AutoField()
    name = CharField()

    class Meta:
        table_name = 'difficulty'


class Riddles(BaseModel):
    riddle_id = AutoField()
    question = TextField()
    answer = CharField()
    difficulty = ForeignKeyField(column_name='difficulty_id', field='difficulty_id', model=Difficulty, null=True)

    class Meta:
        table_name = 'riddles'


class Users(BaseModel, UserMixin):
    user_id = AutoField()
    username = CharField()
    password = CharField()
    email = CharField(null=True)
    name = TextField()
    birthday = DateField()
    points = IntegerField(constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'users'


class UsersRiddles(BaseModel):
    user = ForeignKeyField(column_name='user_id', field='user_id', model=Users)
    riddle = ForeignKeyField(column_name='riddle_id', field='riddle_id', model=Riddles)

    class Meta:
        table_name = 'users_riddles'
        primary_key = False


TABLES = [
    Difficulty, Riddles, Users, UsersRiddles
]


def reset_db():
    with database.connection_context():
        database.create_tables(TABLES, safe=True)
        database.commit()

def update_difficulties():
    with database.connection_context():
        # database.drop_tables(Difficulty)
        # database.create_tables([Difficulty], safe=True)
        difficulties = [
            {'name': 'Easy'},
            {'name': 'Normal'},
            {'name': 'Hard'}
        ]
        Difficulty.insert_many(difficulties).execute()
        database.commit()


    
def update_riddles():
    with database.connection_context():
        # database.create_tables([Riddles], safe=True)
        data = pandas.read_csv('riddles.csv')
        questions = data.QUESTIONS.tolist()
        answers = data.ANSWERS.tolist()
        qa_dict = dict(zip(questions, answers))
        dicts_list = []
        for k, v in qa_dict.items():
            dicts_list.append({'question': k, 'answer': v, 'difficulty': randint(1, 3)})
        Riddles.insert_many(dicts_list).execute()
        database.commit()


# reset_db()
# update_difficulties()
# update_riddles()
