from peewee import *
import pandas
from flask_login import UserMixin
from random import randint


database = SqliteDatabase('riddles.db')


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
    answer = CharField()
    difficulty = ForeignKeyField(column_name='difficulty_id', field='difficulty_id', model=Difficulty, null=True)
    question = CharField()
    riddle_id = AutoField()

    class Meta:
        table_name = 'riddles'


class Users(BaseModel, UserMixin):
    birthday = DateField()
    email = CharField(null=True)
    password = CharField()
    points = IntegerField(constraints=[SQL("DEFAULT 0")])
    user_id = AutoField()
    username = CharField()
    name = TextField()

    class Meta:
        table_name = 'users'


class UsersRiddles(BaseModel):
    riddle = ForeignKeyField(column_name='riddle_id', field='riddle_id', model=Riddles)
    user = ForeignKeyField(column_name='user_id', field='user_id', model=Users)

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
        database.drop_tables(Difficulty)
        database.create_tables([Difficulty], safe=True)
        difficulties = [
            {'name': 'Easy'},
            {'name': 'Normal'},
            {'name': 'Hard'}
        ]
        Difficulty.insert_many(difficulties).execute()
        database.commit()


    
def update_riddles():
    with database.connection_context():
        database.create_tables([Riddles], safe=True)
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