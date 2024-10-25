from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from database import get_monogodb_client

client = get_monogodb_client()

db = client['Hand_Sign_Language_HMI_Lab']


def get_collection(collection_name):
    collection = db[collection_name]
    return collection


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
