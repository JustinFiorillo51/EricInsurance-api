import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

    #   SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'mssql+pyodbc://EKInsuranceSQL:sL3GzduA9Rkm@172.105.8.29:1433/EKiser-Insurance-TablesSQL?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no')
    
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'mssql+pyodbc://EKInsuranceSQL:sL3GzduA9Rkm@172.105.8.29:1433/EKiser-Insurance-TablesSQL?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 5,
        'pool_timeout': 60,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'echo': True,
    }
