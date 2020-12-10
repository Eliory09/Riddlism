import os
from random import randint

import pandas
from dotenv import load_dotenv
from flask_login import UserMixin
from peewee import *
from playhouse.db_url import connect


load_dotenv()
db_proxy = Proxy()
database = connect(os.getenv('DATABASE_URL'))
db_proxy.initialize(database)


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


def reset_db(path):
    """Reset the database - truncate all tables and recreate them with initialized data.
    Args:
        path (str): Path to riddles.csv data file.
    Returns:
        None.
    """
    if path is None:
        print("Please specify riddles.csv path. Aborting...")
    else:
        with database.connection_context():
            ans = input("Running this will truncate ALL tables on the database. Are you sure? (y/n): ")
            try:
                if ans == "y":
                    database.drop_tables(TABLES)
                    database.create_tables(TABLES, safe=True)
                    # This function calls commiting database.
                    update_difficulties()
                    update_riddles(path)
                else:
                    print("Aborting...")
            except (TypeError, FileNotFoundError) as e:
                print(e)
                print("An error occured. Check your riddles.csv file or input path.")
            


def update_difficulties():
    """Updates difficulty table."""
    with database.connection_context():
        difficulties = [
            {'name': 'Easy'},
            {'name': 'Normal'},
            {'name': 'Hard'}
        ]
        Difficulty.insert_many(difficulties).execute()
        database.commit()

    
def update_riddles(path):
    """Updates riddles table."""
    with database.connection_context():
        data = pandas.read_csv(path)
        questions = data.QUESTIONS.tolist()
        answers = data.ANSWERS.tolist()
        qa_dict = dict(zip(questions, answers))
        dicts_list = []
        for k, v in qa_dict.items():
            dicts_list.append({'question': k, 'answer': v, 'difficulty': randint(1, 3)})
        Riddles.insert_many(dicts_list).execute()
        database.commit()


# if __name__ == "__main__":
#     path = 'riddles.csv'
#     reset_db(path)
#     update_difficulties()
#     update_riddles(path)
