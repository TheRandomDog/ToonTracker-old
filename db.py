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

    def __init__(self, file_name, tables=[]):
        self.file_name = file_name

        self.conn = sqlite3.connect(file_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

        self.tables = {}
        for table in tables:
            table.conn = self.conn
            table.c = self.c
            table.create()
            self.tables[table.name] = table

    def create_table(self, table_name, arguments={}, error_if_existing=False):
        table = DatabaseTable(table_name, arguments)
        table.conn = self.conn
        table.c = self.c
        table.create(error_if_existing)
        return table

    def __del__(self):
        self.conn.close()


class DatabaseTable:
    def __init__(self, table_name, arguments={}):
        self.conn = None
        self.c = None
        self.name = table_name
        self.arguments = arguments

    @staticmethod
    def get_where_sanitization(raw_where, where):
        """
            SQL Operation methods have two options for inputting WHERE clauses:
                They can do it with `raw_where`, no sanitization, if the value is hard-coded or trusted.
                Or it can be sanitized with `where`, if the value is variable or untrusted.

            When using `raw_where`, you can enter a string or a list of WHERE clauses (that will be joined together by ANDs).
                e.g. table.select(raw_where='id=1')
                e.g. table.select(raw_where='id=1' AND 'name="Monty"')
                e.g. table.select(raw_where=['id=1', 'name="Monty"'])
            When using `where`, you create a list or a list of lists (that will be joined together by ANDs).
            You enter the column information first with the values substituted with a question mark, then the rest of the list contains the values.
                e.g. table.select(where=['id=?', 1])
                e.g. table.select(where=['id=? AND name=?'], 1, "Monty"')
                e.g. table.select(where=[['id=?', 1], ['name=?', "Monty"]])

            WHERE queries being joined together by ANDs are strung together in the SQL Operation methods themselves.
        """

        sanitize = bool(where)  # are we sanitzing? (is there something in where?)
        where_keys = []  # the where queries, columns and scuh
        where_values = []  # the values that are being substituted

        if sanitize:
            if type(where[0]) == str:  # If it's not a list of lists, make it one 
                where = [where]
            for w in where:  # For every list in major list, take the where query and extend the values list
                where_keys.append(w[0])
                where_values.extend(w[1:])
        else:
            if type(raw_where) == str: raw_where = [raw_where]  # if it's not a list, make it one
            where_keys = raw_where  # we're not sanitizing, so just put in the keys, and not values
        return where_keys, where_values
        
    def create(self, error_if_existing=False):
        list_args = []
        for arg_name, arg_type in self.arguments.items():
            if type(arg_type) == list:
                arg_type_params = []
                for param in arg_type:
                    if param in DatabaseManager.TYPES or param in DatabaseManager.PARAMS:
                        arg_type_params.append(param)
                    elif arg_type_params[0] in [DatabaseManager.TEXT, DatabaseManager.BLOB]:
                        arg_type_params.append('DEFAULT "{}"'.format(param))
                    else:
                        arg_type_params.append('DEFAULT {}'.format(param))
                arg_type = ' '.join(arg_type_params)

            arg = f'{arg_name} {arg_type}'
            list_args.append(arg)
        try:
            command = 'CREATE TABLE {}({})'.format(self.name, ', '.join(list_args))
            self.c.execute(command)
            self.conn.commit()
        except sqlite3.OperationalError as e:
            if error_if_existing or 'exists' not in str(e):
                raise e

    def select(self, columns='*', *, raw_where=[], where=[], limit=None):
        fetch = self.c.fetchone if limit == 1 else self.c.fetchall

        if type(columns) == list:
            columns = ', '.join(columns)
        where_keys, where_values = self.get_where_sanitization(raw_where, where)

        command = 'SELECT {} FROM {}'.format(columns, self.name)
        if where_keys:
            command += ' WHERE '
            command += ' AND '.join(where_keys)
        if limit:
            command += ' LIMIT {}'.format(limit)
        self.c.execute(command, where_values)
        return fetch()

    def delete(self, *, raw_where=[], where=[], limit=None):
        where_keys, where_values = self.get_where_sanitization(raw_where, where)

        command = 'DELETE FROM {} WHERE '.format(self.name)
        command += ' AND '.join(where_keys)
        if limit:
            command += ' LIMIT {}'.format(limit)
        self.c.execute(command, where_values)
        self.conn.commit()

    def update(self, *, raw_where=[], where=[], **kwargs):
        where_keys, where_values = self.get_where_sanitization(raw_where, where)

        command = 'UPDATE {} SET {}'.format(
            self.name,
            ', '.join([column + '=?' for column in kwargs.keys()])
        )
        if where_keys:
            command += ' WHERE '
            command += ' AND '.join(where_keys)
        self.c.execute(command, list(kwargs.values()) + where_values)
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