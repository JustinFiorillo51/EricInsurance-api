from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, **Config.SQLALCHEMY_ENGINE_OPTIONS)


# Establish connection
# with engine.connect() as connection:
#     # Define the query
#     query = """
#     SELECT top 1 * 
#     FROM [tblStates]
#     ORDER BY StateName DESC
#     """
        
#     # Execute query
#     result = connection.execute(query)
        
#     # Fetch all rows
#     rows = result.fetchall()
        
#     # Check if results are empty
#     if not rows:
#         print("No results found for the query.")
#     else:
#         # Print results
#         print("High-Volume Trades (Potential Institutional Buying):")
#         for row in rows:
#             print(row)
            

Session = sessionmaker(bind=engine)


Model = declarative_base()


# class User(Model):
#     __tablename__ = 'Users'
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100), nullable=False)
#     email = Column(String(100), nullable=False)
