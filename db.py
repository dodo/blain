

from sqlalchemy import (create_engine, Table, MetaData, Column, Integer,
                        String, Unicode, Text, UnicodeText, Date, Numeric,
                        Time, Float, DateTime, Interval, Binary, Boolean,
                        PickleType)
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.interfaces import PoolListener



class SetTextFactory(PoolListener):
     def connect(self, dbapi_con, con_record):
         dbapi_con.text_factory = str



class Database:

    def __init__(self, type = "sqlite", location = ":memory:"):
        if type == 'sqlite':
            location = "/" + location
        self.models = {}
        self.type = type
        self.location = location
        self.name = type + '://' + location
        self.engine = create_engine(self.name)#, listeners=[SetTextFactory()])
        self.session = sessionmaker(bind=self.engine)()
        self.column_mapping = {'string': String,       'str': String,
                              'integer': Integer,      'int': Integer,
                              'unicode': Unicode,     'text': Text,
                          'unicodetext': UnicodeText, 'date': Date,
                              'numeric': Numeric,     'time': Time,
                                'float': Float,   'datetime': DateTime,
                             'interval': Interval,  'binary': Binary,
                              'boolean': Boolean,     'bool': Boolean,
                           'pickletype': PickleType}

    def find(self, name):
        return self.models[name]

    def addModel(self, name, model):
        self.models[name] = model
        setattr(self, name, model)



class ClassConstructor(type):
    def __new__(cls, name, bases, dct):
        return type.__new__(cls, name, bases, dct)
    def __init__(cls, name, bases, dct):
        super(ClassConstructor, cls).__init__(name, bases, dct)



def model(db, model_name, **kwargs):
    # Functions for the class
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__dict__[k] = v
    def add(self):
        db.session.add(self)
        return self
    def save(self):
        s = db.session
        if self not in s: s.add(self)
        s.commit()
        return self
    def __repr__(self):
        return '<%s: id = %s>' %(self.__name__, self.id)
    def __str__(self):
        return '<%s: id = %s>' %(self.__name__, self.id)
    # Some static functions for the class
    def find_func(cls, *args):
        return db.session.query(cls, *args)
    # Build the class's __dict__
    cls_dict = {'__init__': __init__,
                'add':      add,
                'save':     save,
                '__name__': model_name,
                '__repr__': __repr__,
                '__str__':  __str__,
                'find':     None,       # Defined later
               }
    # Parse kwargs to get column definitions
    cols = [ Column('id', Integer, primary_key=True), ]
    for k, v in kwargs.items():
        if callable(v):
            cls_dict[k] = v
        elif isinstance(v, Column):
            if not v.name: v.name = k
            cols.append(v)
        elif type(v) == str:
            v = v.lower()
            if v in db.column_mapping: v = db.column_mapping[v]
            else: raise NameError("'%s' is not an allowed database column" %v)
            cols.append(Column(k, v))
    # Create the class
    tmp = ClassConstructor(model_name, (object,), cls_dict)
    # Add the functions that need an instance of the class
    tmp.find = staticmethod(lambda *args: find_func(tmp, *args))
    # Create the table
    metadata = MetaData()
    tmp_table = Table(model_name + 's', metadata, *cols)
    metadata.create_all(db.engine)
    # Map the table to the created class
    mapper(tmp, tmp_table)
    # Track the class
    db.addModel(model_name, tmp)
    return tmp
