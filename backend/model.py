import mysql.connector

class Model:
    def __init__(self, host_arg, user_arg, password_arg, database_arg = None):
        # creates a mysql.connector object that handles all queries to the DB
        self.db = mysql.connector.connect(
            host=host_arg,
            user=user_arg,
            password = password_arg,
            database = database_arg
        )
        self.cursor = self.db.cursor()

    ########################## USER MANAGEMENT CRUD OPS ################################

    def save_user(self, voiceit_id, azure_ver_id="", azure_iden_id="", name=""):
        # save user user to the user table
        try:
            if azure_iden_id and azure_ver_id:
                sql = """
                INSERT INTO user (name, voiceit_id, azure_iden_id, azure_ver_id, 
                    created, voiceit_enrolled, azure_identification_enrolled, azure_verification_enrolled)
                    VALUES (%s, %s, %s, %s, NOW(), false, false, false)
                """
                params = (name, voiceit_id, azure_iden_id, azure_ver_id, )
            else:
                sql = """
                INSERT INTO user (name, voiceit_id, created, voiceit_enrolled, 
                    azure_identification_enrolled, azure_verification_enrolled) 
                    values (%s, %s, NOW(), false, false, false)
                """
                params = (name, voiceit_id, )

            self.cursor.execute(sql, params)
            self.db.commit()
            return "success"
        except Exception as e:
            print(str(e))
            return str(e)


    def get_user(self, voiceit_id):
        # returns user tuple of the corresponding user
        try:
            sql = "SELECT * FROM user WHERE voiceit_id = %s"
            param = (voiceit_id, )
            self.cursor.execute(sql, param)
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(str(e))
            return str(e)


    def get_users(self):
        # returns list of tuples from all users in the user table
        try:
            sql = "SELECT * FROM user"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(str(e))
            return str(e)


    def update_user(self, voiceit_id, **kwargs):
        """
        updates either name and/or enrollment status
        optional arguments ##kwargs define the columns and values to be updated
        name of argument is the column and value of argument is the value to be set in the column
        """
        
        try:
            st = ""
            for key, value in kwargs.items():
                st += str(key)+"='"+str(value)+"',"

            st = st.strip(",")

            sql = "UPDATE user SET {0} WHERE voiceit_id = '{1}'".format(st, voiceit_id)
            print("db says: ", sql)
            self.cursor.execute(sql)
            self.db.commit()
            return "success"
        except Exception as e:
            return str(e)


    def delete_user(self, voiceit_id):
        try:
            sql = "DELETE FROM user WHERE voiceit_id = %s"
            print("voiceit id from db: ", voiceit_id)
            param = (voiceit_id, )
            self.cursor.execute(sql, param)
            self.db.commit()
            return "success"
        except Exception as e:
            return str(e)

    ########################## GROUP MANAGEMENT CRUD OPS ################################
    
    def create_group(self, name, voiceit_id=None):
        # create group with respective voiceit id and date
        try:
            sql = """
            INSERT INTO vgroup (group_name, voiceit_id, created) 
                values (%s, %s, NOW())
            """
            values = (name, voiceit_id)
            self.cursor.execute(sql, values)
            self.db.commit()
            return "success"
        except Exception as e:
            return str(e)


    def get_group(self, group_name):
        # get tuple of respective group
        try:
            sql = "SELECT * FROM vgroup WHERE name = %S"
            params = (group_name, )
            self.cursor.execute(sql, params)
            result = self.cursor.fetchone()
        except Exception as e:
            print(str(e))
            return str(e)


    def get_groups(self):
        # get list of tuples of all groups
        try:
            sql = "SELECT * FROM vgroup"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(str(e))
            return str(e)     
    

    def get_users_from_group(self, group_id):
        # gets all users belonging to a group
        try:
            sql = """SELECT * FROM user
                        WHERE p_key in (SELECT user_id FROM user_group
                            WHERE group_id = %s)"""

            params = (group_id,  )
            self.cursor.execute(sql, params)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(str(e))
            return str(e)


    def add_user_to_group(self, userId, groupId=1, name=""):
        #user is added to group by representing the relationship in the DB
        # many to many relationship, so a third table user_group is used to represent relationshps
        # default group is "general" if no group Id is passed
        try:
            sql = """
            INSERT INTO user_group (user_id, group_id)
                VALUES (%s, %s)
            """
            values = (userId, groupId)
            self.cursor.execute(sql, values)
            self.db.commit()
            return "success"
        except Exception as e:
            return str(e)


    def update_group(self, groupId, name):
        # only name can be updated, given a groupId
        try:
            sql = "UPDATE vgroup SET group_name = '{0}' WHERE p_key = {1}".format(name, groupId)
            self.cursor.execute(sql)
            self.db.commit()
            return "success"
        except Exception as e:
            raise e


    def remove_user_from_group(self, userId, groupId=1):
        try:
            user = self.get_user(userId)
            uid = user[0]
            sql = "DELETE FROM user_group WHERE user_id = %s and group_id = %s"
            params = (uid, groupId)
            self.cursor.execute(sql, params)
            self.db.commit()
            return "success"
        except Exception as e:
            return str(e)


    def delete_group(self, name):
        try:
            sql = "DELETE FROM vgroup WHERE group_name = %s"
            params = (name, )
            self.cursor.execute(sql, params)
            self.db.commit()
            
            return "success"
        except Exception as e:
            print(str(e))
            return str(e)

