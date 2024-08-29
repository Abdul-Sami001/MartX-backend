import os
import re
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Populate the database from seed.sql"

    def handle(self, *args, **kwargs):
        # Get the path to the seed.sql file
        file_path = os.path.join(os.path.dirname(__file__), "seed.sql")

        # Read the contents of the seed.sql file
        with open(file_path, "r") as file:
            sql_content = file.read()

        # Define the tables you want to clear before inserting
        # if you are getting unique constraint errors use this
        tables_to_clear = [
            "store_collection",
            # add other tables here
        ]

        # Clear the tables
        with connection.cursor() as cursor:
            for table in tables_to_clear:
                cursor.execute(f"DELETE FROM {table};")
                cursor.execute(f'DELETE FROM sqlite_sequence WHERE name="{table}";')

        # Split the SQL content into individual statements using regex
        statements = re.split(r";\s*", sql_content.strip())

        # Execute each statement separately
        with connection.cursor() as cursor:
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)

        self.stdout.write(self.style.SUCCESS("Database populated successfully"))
