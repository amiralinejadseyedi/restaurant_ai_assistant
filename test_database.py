from sqlalchemy import text
from app.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        )

        print("Database connection successful!")

        for row in result:
            print("Database:", row[0])
            print("User:", row[1])

except Exception as error:
    print("Database connection failed!")
    print(error)



    