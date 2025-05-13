from tools.tools.db_pool import DatabasePool


# получение списка стран по именам
def get_countries():
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT cntry_name FROM country
            ORDER BY cntry_name;"""
        cursor.execute(query, )
        countries = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        countries = []
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return countries


# получение id страны по заданному имени из БД
def get_one_id(country):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT id_cntry FROM country
            WHERE cntry_name = %s;
            """
        cursor.execute(query, (country,))
        result = cursor.fetchone()
        if not result:
            raise Exception
        id_cntry = result[0]
    except Exception as e:
        id_cntry = []
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return id_cntry


# получение имен и id всех стран из БД
def get_all_id():
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT cntry_name, id_cntry FROM country ORDER BY cntry_name;"""
        cursor.execute(query, )
        countries = cursor.fetchall()
        if not countries:
            raise Exception
    except Exception as e:
        countries = []
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return countries


# получение заданной даты из БД
def get_date(from_table, is_end):
    query = {
        True: f"""SELECT dte FROM {from_table}
                ORDER BY dte DESC LIMIT 1;
                """,
        False: f"""SELECT dte FROM {from_table}
                ORDER BY dte LIMIT 1;
                """
    }
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        cursor.execute(query[is_end], )
        result = cursor.fetchone()
        if not result:
            raise Exception
        dte = result[0]
    except Exception as e:
        dte = []
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return dte
