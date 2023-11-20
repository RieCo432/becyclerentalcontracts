from datetime import datetime
import bcrypt
from config import db_user, db_pwd, db_host, db_port
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.dbref import DBRef
from models.user import User


def _break_dict(dictionary: dict) -> list:
    return [{key: value} for key, value in dictionary.items()]

def _build_or_filter(list_of_filters: list) -> dict:
    return {"$or": list_of_filters}

def _build_and_filter(list_of_filters: list) -> dict:
    return {"$and": list_of_filters}

def _build_contract_filter(**contract_data) -> dict:
    qualifiers = []
    for key in contract_data:
        if key == "bike":
            qualifiers.append({"bike.$id": {"$in": contract_data["bike"]}})
        elif key == "person":
            qualifiers.append({"person.$id": {"$in": contract_data["person"]}})
        else:
            qualifiers.append({key: contract_data[key]})

    contract_filters = _build_or_filter(qualifiers)
    return contract_filters

def _get_collection(collection: str):
    client = MongoClient(f"mongodb://{db_user}:{db_pwd}@{db_host}:{db_port}")
    db = client["becycleDB"]
    return db[collection]

def _deref(ref: DBRef) -> dict:
    client = MongoClient(f"mongodb://{db_user}:{db_pwd}@{db_host}:{db_port}")
    db = client["becycleDB"]
    return db.dereference(ref)

def get_persons_count(**person_data) -> int:
    person_filter = _build_or_filter(_break_dict(person_data))
    persons = _get_collection("persons")
    return persons.count_documents(person_filter)

def get_persons(**person_data) -> list:
    person_filter = _build_or_filter(_break_dict(person_data))
    persons = _get_collection("persons")
    return [person for person in persons.find(person_filter)]

def get_one_person(**person_data) -> dict:
    person_filter = _build_and_filter(_break_dict(person_data))
    persons = _get_collection("persons")
    return persons.find_one(person_filter)

def get_bikes_count(**bike_data) -> int:
    bike_filter = _build_or_filter(_break_dict(bike_data))
    bikes = _get_collection("bikes")
    return bikes.count_documents(bike_filter)

def get_bikes(**bike_data) -> list:
    bike_filter = _build_or_filter(_break_dict(bike_data))
    bikes = _get_collection("bikes")
    return [bike for bike in bikes.find(bike_filter)]

def get_one_bike(**bike_data) -> dict:
    bike_filter = _build_and_filter(_break_dict(bike_data))
    bikes = _get_collection("bikes")
    return bikes.find_one(bike_filter)

def add_person(**person_data) -> ObjectId:
    persons = _get_collection("persons")
    return persons.insert_one(person_data).inserted_id

def add_bike(**bike_data) -> ObjectId:
    bikes = _get_collection("bikes")
    return bikes.insert_one(bike_data).inserted_id

def add_contract(**contract_data) -> ObjectId:
    contracts = _get_collection("contracts")
    return contracts.insert_one(contract_data).inserted_id

def get_contracts_count(**contract_data) -> int:
    contracts = _get_collection("contracts")
    return contracts.count_documents(_build_contract_filter(**contract_data))

def get_contract_one(**contract_data) -> dict:
    contracts = _get_collection("contracts")
    contract = contracts.find_one(_build_contract_filter(**contract_data))
    for key in contract:
        if key == "bike" or key == "person":
            contract[key] = _deref(contract[key])

    return contract

def get_contracts(**contract_data) -> list:
    contracts_collection = _get_collection("contracts")
    if contract_data:
        contracts_filter = _build_contract_filter(**contract_data)
    else:
        contracts_filter = {}
    contracts = [contract for contract in contracts_collection.find(contracts_filter)]
    for contract in contracts:
        for key in contract:
            if key == "bike" or key == "person":
                contract[key] = _deref(contract[key])
    return contracts

def update_contract_one(**contract_data) -> None:
    if "_id" not in contract_data:
        raise KeyError("Supplied Contract Data must have an _id")
    new_contract_data = {key: value for key, value in contract_data.items() if key != "_id"}
    contracts = _get_collection("contracts")
    contracts.update_one({"_id": contract_data["_id"]}, {"$set": new_contract_data})

def update_person_one(**person_data) -> None:
    if "_id" not in person_data:
        raise KeyError("Supplied Person Data must have an _id")
    new_person_data = {key: value for key, value in person_data.items() if key != "_id"}
    persons_collection = _get_collection("persons")
    persons_collection.update_one({"_id": person_data["_id"]}, {"$set": new_person_data})

def update_bike_one(**bike_data) -> None:
    if "_id" not in bike_data:
        raise KeyError("Supplied Bike Data must have an _id")
    new_bike_data = {key: value for key, value in bike_data.items() if key != "_id"}
    bikes_collection = _get_collection("bikes")
    bikes_collection.update_one({"_id": bike_data["_id"]}, {"$set": new_bike_data})

def get_bookkeeping() -> (dict, list):
    contracts_collection = _get_collection("contracts")

    all_entries = []

    for contract in get_contracts():
        all_entries.append(
            {"date": datetime.date(contract["startDate"]), "fullName": contract["person"]["firstName"] + " " +contract["person"]["lastName"],
             "action": "deposit", "deposit_bearer": contract["depositCollectedBy"],
             "deposit_amount": contract["depositAmountPaid"]})

        if contract["returnedDate"] and contract["depositAmountReturned"] and contract["volunteerReceived"] and contract["depositReturnedBy"]:
            all_entries.append(
                {"date": datetime.date(contract["returnedDate"]), "fullName": contract["person"]["firstName"] + " " +contract["person"]["lastName"],
                 "action": "return", "deposit_bearer": contract["depositReturnedBy"],
                 "deposit_amount": -contract["depositAmountReturned"]})

    all_entries.sort(key=lambda e: e["date"])

    book = {}
    date = 0
    for entry in all_entries:
        if entry["date"] != date:
            previous_date = date
            date = entry["date"]

        if date not in book.keys():
            book[date] = {"deposit_bearer_balances": {} if not previous_date else {deposit_bearer: balance for deposit_bearer, balance in book[previous_date]["deposit_bearer_balances"].items() if balance != 0}, "entries": []}
        book[date]["entries"].append(entry)
        if entry["action"] == "deposit":
            if entry["deposit_bearer"] not in book[date]["deposit_bearer_balances"].keys():
                book[date]["deposit_bearer_balances"][entry["deposit_bearer"]] = entry["deposit_amount"]
            else:
                book[date]["deposit_bearer_balances"][entry["deposit_bearer"]] += entry["deposit_amount"]
        elif entry["action"] == "return":
            if entry["deposit_bearer"] not in book[date]["deposit_bearer_balances"].keys():
                raise Exception("Deposit Bearer Should Not Have Any Money")
            else:
                book[date]["deposit_bearer_balances"][entry["deposit_bearer"]] += entry["deposit_amount"]


    return book


def get_deposit_bearer_balance(deposit_bearer):
    contracts_collection = _get_collection("contracts")

    collected_deposits = [contract["depositAmountPaid"] for contract in contracts_collection.find({"depositCollectedBy": deposit_bearer})]
    returned_deposits = [contract["depositAmountReturned"] for contract in contracts_collection.find({"depositReturnedBy": deposit_bearer})]

    total_collected = sum(collected_deposits)
    total_returned = sum(returned_deposits)

    balance = total_collected - total_returned

    return balance


def get_deposit_amount_paid(contract_id: str):
    contracts_collection = _get_collection("contracts")

    contract = contracts_collection.find_one({"_id": ObjectId(contract_id)})

    return contract["depositAmountPaid"]


def get_user_hashed_password(username: str):
    users_collection = _get_collection("users")

    if check_if_username_exists(username):
        return users_collection.find_one({"username": username})["password"]
    else:
        return bcrypt.hashpw("", bcrypt.gensalt())


def update_user_password(username: str, hashed_password: str):
    users_collection = _get_collection("users")

    return users_collection.update_one({"username": username}, {"$set": {"password": hashed_password}}).acknowledged

def get_user_by_username(username: str):
    users_collection = _get_collection("users")

    return User(users_collection.find_one({"username": username}))

def get_user_by_id(id: str):
    users_collection = _get_collection("users")

    return User(users_collection.find_one({"_id": ObjectId(id)}))

def check_if_username_exists(username: str):
    users_collection = _get_collection("users")

    return users_collection.count_documents({"username": username}) == 1


def get_all_users():
    users_collection = _get_collection("users")
    all_users = [user_data for user_data in users_collection.find()]

    return [User(user_data) for user_data in all_users]


def add_user(**user_data):
    users_collection = _get_collection("users")

    return users_collection.insert_one(user_data).acknowledged

def update_user(**updated_user_data):
    users_collection = _get_collection("users")

    return users_collection.update_one({"username": updated_user_data["username"]}, {"$set": updated_user_data}).acknowledged



