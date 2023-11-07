from datetime import datetime
from config import db_user, db_pwd, db_host, db_port
from pymongo import MongoClient
from bson.objectid import ObjectId


def _break_dict(dictionary: dict) -> list:
    return [{key: value} for key, value in dictionary.items()]

def _build_or_filter(list_of_filters: list) -> dict:
    return {"$or": list_of_filters}

def _build_and_filter(list_of_filters: list) -> dict:
    return {"$and": list_of_filters}

def _build_contract_filter(**contract_data) -> dict:
    contract_fields = {}
    for field, value in contract_data.items():
        if str(value) == "" or value is None or str(value).lower() == "none":
            continue
        root_field = field.split(".")[0]
        if root_field not in contract_fields:
            contract_fields[root_field] = {}
        contract_fields[root_field][field] = value

    sub_filters = [_build_or_filter(_break_dict(data)) for data in contract_fields.values()]
    final_filter = _build_and_filter(sub_filters)
    return final_filter

def _get_collection(collection: str):
    client = MongoClient(f"mongodb://{db_user}:{db_pwd}@{db_host}:{db_port}")
    db = client["becycleDB"]
    return db[collection]

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
    return contracts.find_one(_build_contract_filter(**contract_data))

def get_contracts(**contract_data) -> list:
    contracts = _get_collection("contracts")
    return [contract for contract in contracts.find(_build_contract_filter(**contract_data))]

def update_contract_one(**contract_data) -> None:
    if "_id" not in contract_data:
        raise KeyError("Supplied Contract Data must have an _id")
    new_contract_data = {key: value for key, value in contract_data.items() if key != "_id"}
    contracts = _get_collection("contracts")
    contracts.update_one({"_id": contract_data["_id"]}, {"$set": new_contract_data})

def get_bookkeeping() -> (dict, list):
    contracts_collection = _get_collection("contracts")

    all_entries = []

    for contract in contracts_collection.find():
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



