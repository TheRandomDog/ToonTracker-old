import sqlite3

class DatabaseManager:
    NULL = 'NULL'
    INT = 'INTEGER'
    REAL = 'REAL'
    TEXT = 'TEXT'
    BLOB = 'BLOB'
    BOOLEAN = 'INTEGER'

    PRIMARY_KEY = 'PRIMARY KEY'

    def __init__(self, fileName, tables=[]):
        self.fileName = fileName

        self.conn = sqlite3.connect(fileName, check_same_thread=False)
        self.c = self.conn.cursor()

        self.tables = {}
        for table in tables:
            table.conn = self.conn
            table.c = self.c
            table.create()
            self.tables[table.name] = table

    def createTable(self, tableName, arguments={}, errorIfExisting=False):
        table = DatabaseTable(tableName, arguments)
        table.conn = self.conn
        table.c = self.c
        table.create(errorIfExisting)
        return table

    def __del__(self):
        self.conn.close()


class DatabaseTable:
    def __init__(self, tableName, arguments={}):
        self.conn = None
        self.c = None
        self.name = tableName
        self.arguments = arguments

    def create(self, errorIfExisting=False):
        listArgs = []
        for argName, argType in self.arguments.items():
            if type(argType) == list:
                argType = ' '.join(argType)
            arg = f'{argName} {argType}'
            listArgs.append(arg)
        try:
            command = 'CREATE TABLE {}({})'.format(self.name, ', '.join(listArgs))
            print(command)
            self.c.execute(command)
            self.conn.commit()
        except sqlite3.OperationalError as e:
            print(e)
            if errorIfExisting:
                raise e

    def select(self, columns='*', where=[], limit=None):
        if type(columns) == list:
            columns = ', '.join(columns)
        if type(where) == str:
            where = [where]

        command = 'SELECT {} FROM {}'.format(columns, self.name)
        if where:
            command += ' WHERE '
            command += ' AND '.join(where)
        if limit:
            command += ' LIMIT {}'.format(limit)
        print(command)
        self.c.execute(command)
        return self.c.fetchall()

    def insert(self, **kwargs):
        columns = []
        values = []

        for argument in self.arguments.keys():
            if argument in kwargs:
                columns.append(argument)
                values.append(kwargs[argument])

        command = 'INSERT INTO {} ({}) VALUES ({})'.format(
            self.name, 
            ','.join(columns),
            ','.join(['?' for _ in range(len(values))])
        )
        print(command)
        self.c.execute(command, values)
        self.conn.commit()