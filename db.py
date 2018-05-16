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

    @staticmethod
    def getWhereSanitization(rawWhere, where):
        """
            SQL Operation methods have two options for inputting WHERE clauses:
                They can do it with `rawWhere`, no sanitization, if the value is hard-coded or trusted.
                Or it can be sanitized with `where`, if the value is variable or untrusted.

            When using `rawWhere`, you can enter a string or a list of WHERE clauses (that will be joined together by ANDs).
                e.g. table.select(rawWhere='id=1')
                e.g. table.select(rawWhere='id=1' AND 'name="Monty"')
                e.g. table.select(rawWhere=['id=1', 'name="Monty"'])
            When using `where`, you create a list or a list of lists (that will be joined together by ANDs).
            You enter the column information first with the values substituted with a question mark, then the rest of the list contains the values.
                e.g. table.select(where=['id=?', 1])
                e.g. table.select(where=['id=? AND name=?'], 1, "Monty"')
                e.g. table.select(where=[['id=?', 1], ['name=?', "Monty"]])

            WHERE queries being joined together by ANDs are strung together in the SQL Operation methods themselves.
        """

        sanitize = bool(where)  # are we sanitzing? (is there something in where?)
        whereKeys = []  # the where queries, columns and scuh
        whereValues = []  # the values that are being substituted

        if sanitize:
            if type(where[0]) == str:  # If it's not a list of lists, make it one 
                where = [where]
            for w in where:  # For every list in major list, take the where query and extend the values list
                whereKeys.append(w[0])
                whereValues.extend(w[1:])
        else:
            if type(rawWhere) == str: rawWhere = [rawWhere]  # if it's not a list, make it one
            whereKeys = rawWhere  # we're not sanitizing, so just put in the keys, and not values
        return whereKeys, whereValues
        
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

    def cleanSelect(self, columns='*', *, rawWhere=[], where=[], limit=10):
        result = []
        rowFormat = ''
        for argument in self.arguments.keys():
            self.c.execute('SELECT MAX(LENGTH({1})) AS MLS FROM {0}'.format(self.name, argument))
            selection = self.c.fetchone()
            valueLength = selection['MLS'] if selection else 0
            #argLengths[argument] = max(len(argument), valueLength)

            rowFormat += '{:>%d}' % max(len(argument), valueLength)
        result.append(rowFormat.format(*tuple(self.arguments.keys())))

        selection = self.select(columns, rawWhere, limit)
        if limit == 1: selection = [selection]
        for row in selection:
            result.append(rowFormat.format(*[row[arg] for arg in self.arguments.keys()]))

        return '\n'.join(result)

    def select(self, columns='*', *, rawWhere=[], where=[], limit=None):
        fetch = self.c.fetchone if limit == 1 else self.c.fetchall

        if type(columns) == list:
            columns = ', '.join(columns)
        whereKeys, whereValues = self.getWhereSanitization(rawWhere, where)

        command = 'SELECT {} FROM {}'.format(columns, self.name)
        if whereKeys:
            command += ' WHERE '
            command += ' AND '.join(whereKeys)
        if limit:
            command += ' LIMIT {}'.format(limit)
        self.c.execute(command, whereValues)
        return fetch()

    def delete(self, *, rawWhere=[], where=[], limit=None):
        whereKeys, whereValues = self.getWhereSanitization(rawWhere, where)

        command = 'DELETE FROM {} WHERE '.format(self.name)
        command += ' AND '.join(whereKeys)
        if limit:
            command += ' LIMIT {}'.format(limit)
        self.c.execute(command, whereValues)
        self.conn.commit()

    def update(self, *, rawWhere=[], where=[], **kwargs):
        whereKeys, whereValues = self.getWhereSanitization(rawWhere, where)

        command = 'UPDATE {} SET {}'.format(
            self.name,
            ', '.join([column + '=?' for column in kwargs.keys()])
        )
        if whereKeys:
            command += ' WHERE '
            command += ' AND '.join(whereKeys)
        self.c.execute(command, list(kwargs.values()) + whereValues)
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