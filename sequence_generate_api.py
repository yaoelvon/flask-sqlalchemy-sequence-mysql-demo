# -*- coding: utf-8 -*-

import os
import sys
import datetime
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import get_debug_queries
from flask_sqlalchemy import SignallingSession
from sqlalchemy import Index

if len(sys.argv) >= 2 and sys.argv[1] and int(sys.argv[1]):
    run_port = int(sys.argv[1])
else:
    run_port = 5000

basedir = os.path.abspath(os.path.dirname(__file__))
# 创建一个对接mysql的引擎（使用sqlalchemy原生方法）
# engine = create_engine('mysql+pymysql://root:password@localhost:4040/auth', echo=False)

app = Flask(__name__)
# 使用sqlite3数据库
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, './dbTest.db')
# 使用mysql数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/auth'

app.config['SECRET_KEY'] = '\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16'
# 将SQLALCHEMY_RECORD_QUERIES或DEBUG改为True，使得record_queries函数运行，打印出sql语句
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
app.config['DEBUG'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# 设置SQLALCHEMY_ECHO为True，使得回显sqlalchemy框架中执行的sql语句
# app.config['SQLALCHEMY_ECHO'] = True
# 设置当前session的配置，然而将autocommit设为1，sqlalchemy框架并没有生效，
# 每次程序运行，首先发送SET AUTOCOMMIT=0，设置Mysql数据库autocommit模式为0：禁止自动提交，
# 以相邻commit之间为一个transaction
# db = SQLAlchemy(app, session_options={'autocommit': 1, 'autoflush': False})
db = SQLAlchemy(app)

# __table_args__语句为type_date字段设置序列，因为for update时，
# 如果query的字段是index的，则锁行(row)；如果query的字段不是Index的，
# 则锁表（table）。锁行的情况下，该表的其他行可以被访问；在锁表的情况下，
# 整个表都被锁住了，无法进行访问。
class Sequence(db.Model):
    __tablename__ = 'sequence'
    __table_args__ = (Index("type_date_index", "type_date"),)
    id = db.Column(db.Integer, primary_key=True)
    type_date = db.Column(db.String(40), nullable=False, default='')
    sequence = db.Column(db.Integer, nullable=False)


# 若没有表，则建表
def init_sequence():
    db.create_all()
    return True


# 根据日期设定，新的一天，需要插入新的记录
def insert_sequence_record(type_date):
    dict_seq = {'type_date': type_date, 'sequence': 0}
    sequence = Sequence(**dict_seq)
    try:
        db.session.add(sequence)
        db.session.commit()
    except Exception, data:
        db.session.rollback()
        current_app.logger.error("Exception=%s, msg=%s", 
                      Exception, data.message)
        return False

    return True    

def sequence_increasing(type_date):
    try:
        q = Sequence.query.filter(Sequence.type_date == type_date).\
            with_lockmode('update').first()
        current_sequence = q.sequence = q.sequence + 1
        db.session.commit() 
    except Exception, data:
        db.session.rollback()
        current_app.logger.error("Exception=%s, msg=%s", 
                      Exception, data.message)
        return 99999
    return current_sequence   

def get_today_date():
    date_list = datetime.date.today().isoformat().split('-')
    today_date = ''
    for dl in date_list:
        today_date += dl

    return today_date    


def today_date_record_if_exist(type_date):
    have_id = Sequence.query.with_entities(Sequence.id).filter(
                Sequence.type_date == type_date).first()
    return have_id

def sequence_exceed_99999(current_sequence):
    return current_sequence > 99999

def integer_2_five_bit_string(int_sequence):
    str_sequence = str(int_sequence)
    zero_number = 5 - len(str_sequence)
    while zero_number:
        str_sequence = '0' + str_sequence
        zero_number = zero_number - 1

    return str_sequence

def get_sequence_ID(what_type):
    today_date = get_today_date()

    type_date = what_type + today_date
    record_exist = today_date_record_if_exist(type_date)
    if not record_exist:
        insert_sequence_record(type_date)

    current_sequence = sequence_increasing(type_date)     

    if sequence_exceed_99999(current_sequence):
        print "sequence exceed 99999"
        return -1

    str_sequence = integer_2_five_bit_string(current_sequence)
    sequence_ID = type_date + str_sequence
    return sequence_ID


@app.route('/increase', methods=['POST'])
def increase():
    global req_count
    if request.method == 'POST':
        sequence_ID = get_sequence_ID('DD')
        print run_port, sequence_ID

        # 打印出sql语句
        # for info in get_debug_queries():
        #     print(info.statement, info.parameters, info.duration) 
                   
        return str(sequence_ID), 200


if __name__ == '__main__':
    init_sequence()
    app.run(port=run_port)