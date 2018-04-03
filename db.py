import sqlite3

class DatabaseManager:
    NULL = 'NULL'
    INT = 'INTEGER'
    REAL = 'REAL'
    TEXT = 'TEXT'
    BLOB = 'BLOB'

    PRIMARY_KEY = 'PRIMARY KEY'
    NOT_NULL = 'NOT NULL'
    DEFAULT = 'DEFAULT'

    TYPES = [NULL, INT, REAL, TEXT, BLOB]
    PARAMS = [PRIMARY_KEY, NOT_NULL, DEFAULT]

    def __init__(self, fileName, tables=[]):
        self.fileName = fileName

        self.conn = sqlite3.connect(fileName, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
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
                argTypeParams = []
                for param in argType:
                    if param in DatabaseManager.TYPES or param in DatabaseManager.PARAMS:
                        argTypeParams.append(param)
                    elif argTypeParams[0] in [DatabaseManager.TEXT, DatabaseManager.BLOB]:
                        argTypeParams.append('DEFAULT "{}"'.format(param))
                    else:
                        argTypeParams.append('DEFAULT {}'.format(param))
                argType = ' '.join(argTypeParams)

            arg = f'{argName} {argType}'
            listArgs.append(arg)
        try:
            command = 'CREATE TABLE {}({})'.format(self.name, ', '.join(listArgs))
            self.c.execute(command)
            self.conn.commit()
        except sqlite3.OperationalError as e:
            if errorIfExisting or 'exists' not in str(e):
                raise e

    def cleanSelect(self, columns='*', where=[], limit=10):
        result = []
        rowFormat = ''
        for argument in self.arguments.keys():
            self.c.execute('SELECT MAX(LENGTH({1})) AS MLS FROM {0}'.format(self.name, argument))
            selection = self.c.fetchone()
            valueLength = selection['MLS'] if selection else 0
            #argLengths[argument] = max(len(argument), valueLength)

            rowFormat += '{:>%d}' % max(len(argument), valueLength)
        result.append(rowFormat.format(*tuple(self.arguments.keys())))

        selection = self.select(columns, where, limit)
        if limit == 1: selection = [selection]
        for row in selection:
            result.append(rowFormat.format(*[row[arg] for arg in self.arguments.keys()]))

        return '\n'.join(result)

    def select(self, columns='*', where=[], limit=None):
        fetch = self.c.fetchone if limit == 1 else self.c.fetchall

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
        self.c.execute(command)
        return fetch()

    def delete(self, where, limit=None):
        if type(where) == str:
            where = [where]

        command = 'DELETE FROM {} WHERE '.format(self.name)
        command += ' AND '.join(where)
        if limit:
            command += ' LIMIT {}'.format(limit)
        self.c.execute(command)
        self.conn.commit()

    def update(self, where=[], **kwargs):
        if type(where) == str:
            where = [where]

        command = 'UPDATE {} SET {}'.format(
            self.name,
            ', '.join([column + '=?' for column in kwargs.keys()])
        )
        if where:
            command += ' WHERE '
            command += ' AND '.join(where)
        self.c.execute(command, list(kwargs.values()))
        self.conn.commit()

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
        self.c.execute(command, values)
        self.conn.commit()
        return self.c.lastrowid