from datetime import datetime
import bcrypt
from dateutil.relativedelta import relativedelta
from config import db_user, db_pwd, db_host, db_port
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.dbref import DBRef
from models.concurrencyEntry import concurrencyEntry
from models.user import User
from math import ceil


client = MongoClient(f"mongodb://{db_user}:{db_pwd}@{db_host}:{db_port}")
db = client["becycleDB"]

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
    return db[collection]


def _deref(ref: DBRef) -> dict:
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
    contracts = []
    for contract in contracts_collection.find(contracts_filter):
        contract["bike"] = _deref(contract["bike"])
        contract["person"] = _deref(contract["person"])
        contracts.append(contract)
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

def get_all_usernames():
    return [user.username for user in get_all_users()]


def add_user(**user_data):
    users_collection = _get_collection("users")

    return users_collection.insert_one(user_data).acknowledged

def update_user(**updated_user_data):
    users_collection = _get_collection("users")

    return users_collection.update_one({"username": updated_user_data["username"]}, {"$set": updated_user_data}).acknowledged


def get_deposit_bearers_usernames():
    users_collection = _get_collection("users")

    deposit_bearers_usernames = [depositBearer["username"] for depositBearer in users_collection.find({"depositBearer": True})]

    return deposit_bearers_usernames

def get_checking_volunteer_usernames():
    users_collection = _get_collection("users")

    checking_volunteers_usernames = [checkingVolunteer["username"] for checkingVolunteer in users_collection.find({"rentalChecker": True})]

    return checking_volunteers_usernames

def add_appointment(**appointment_data):
    appointments_collection = _get_collection("appointments")
    return appointments_collection.insert_one(appointment_data).inserted_id

def complete_email_verification(appointment_id: ObjectId):
    appointments_collection = _get_collection("appointments")
    appointment_filter = _build_and_filter([
        {"emailVerificationCutoff": {"$gte": datetime.now()}},
        {"_id": appointment_id}
    ])
    return appointments_collection.update_one(appointment_filter, {"$set": {"emailVerified": True}}).modified_count

def get_appointment_one(appointment_id: ObjectId):
    appointments_collection = _get_collection("appointments")
    return appointments_collection.find_one({"_id": appointment_id})


def get_appointment_by_ref(ref: str):
    appointments_collection = _get_collection("appointments")
    return appointments_collection.find_one({"ref": ref})

def get_appointment_concurrency():
    appointment_concurrency_collection = _get_collection("appointmentConcurrency")
    return {rule.afterTime: rule.limit for rule in get_appointment_concurrency_entries()}


def get_all_time_slots():
    workshopdays_collction = _get_collection("workshopdays")
    appointment_general_settings = get_appointment_general()

    #  this function will return a list of all available unit time slots in the 4 weeks following 2 days from now
    #  define the period during which to find available slots
    periodStart = datetime.now() + relativedelta(days=appointment_general_settings["bookAhead"]["min"])  # minimum days in advance
    periodEnd = datetime.now() + relativedelta(days=appointment_general_settings["bookAhead"]["max"])  # maximum days in advance

    # find all the scheduled workshop days in the period
    workshopday_filter = _build_and_filter([
        {"date": {"$gte": periodStart}},
        {"date": {"$lte": periodEnd}}
    ])
    workshopdays_datetimes = [workshopday["date"].date() for workshopday in workshopdays_collction.find(workshopday_filter)]

    #  first, build a list of ALL possible time slots from the period start to the period end, starting at a full hour
    timeslots = []
    slot_dateTime = datetime(periodStart.year, periodStart.month, periodStart.day, periodStart.hour, 0)
    #  while the slot datetime is before the end of the period, continue looping
    while slot_dateTime < periodEnd:
        # if the date of the slot is a workshop day, skip it without adding the slot and skip to next day
        if slot_dateTime.date() in workshopdays_datetimes:
            slot_dateTime += relativedelta(days=1)
            continue
        timeslots.append(slot_dateTime)  # add the timeslot to the list
        slot_dateTime += relativedelta(minutes=appointment_general_settings["slotUnit"])  # increase the slot datetime by the slot unit length

    #  now we can weed out all the slots that are on week days when the workshop is not open and return the result
    return [slot for slot in timeslots if slot.weekday() in appointment_general_settings["openingDays"]]


def get_number_of_appointment_slots():
    appointment_concurrency = get_appointment_concurrency()
    #  this function will take the list of all time slots and build a full calendar with concurrent slots based on the
    #  appointment concurrency rules
    all_timeslots = get_all_time_slots()

    #  this will hold the number of allowed appointments at any given time slot
    appointment_slots = {}

    # iterate over all the unique time slots during opening days
    for slot in all_timeslots:
        #  get the concurrency rule applicable to the slot
        #  go over the concurrency rule times and keep the ones that are BEFORE OR AT the current slot time
        #  sort them and extract the last time
        active_concurrency_rule_time = sorted([t for t in appointment_concurrency if t <= slot.time()])[-1]
        # get the number of concurrent appointments allowed at the slot time
        concurrent_appointments_allowed = appointment_concurrency[active_concurrency_rule_time]
        appointment_slots[slot] = concurrent_appointments_allowed

    #  return only those slot times that have more than 0 allowed appointments
    return {slot_time: number_of_slots for slot_time, number_of_slots in appointment_slots.items() if number_of_slots > 0}

def get_number_of_available_slots():
    appointment_general_settings = get_appointment_general()
    #  this function will take the dictionary of how many appointments there are per slot and reduces the number
    #  according to how many appointments are already booked during that slot

    #  get all the appointment slots
    all_appointment_slots = get_number_of_appointment_slots()

    #  get the database collection of booked appointments
    appointments_collection = _get_collection("appointments")

    #  keep track of the number of available appointments for each timeslot
    available_appointment_slots = {}

    # iterate over all the slot datetimes
    for slot_dateTime in all_appointment_slots:
        #  get the number of requested or booked appointments for each slot datetime
        #  only consider:
        #      confirmed appointments
        #      requested ones where the email has been verified
        #      requested ones where the email verification cutoff is still in the future

        slot_filter = _build_and_filter(
            [
                {"startDateTime": {"$lte": slot_dateTime}},
                {"endDateTime": {"$gte": slot_dateTime + relativedelta(minutes=appointment_general_settings["slotUnit"])}},
                {"cancelled": False},
                _build_or_filter(
                    [
                        {"appointmentConfirmed": True},
                        {"emailVerified": True},
                        {"emailVerificationCutoff": {"$gte": datetime.now()}}
                    ]
                )
            ]
        )


        number_of_requested_or_booked_appointments = appointments_collection.count_documents(slot_filter)
        available_appointment_slots[slot_dateTime] = all_appointment_slots[slot_dateTime] - number_of_requested_or_booked_appointments

    #  return the number of available slots per slot time
    return available_appointment_slots


def can_appointment_be_on_slot(available_slots, slot_dateTime, number_of_requested_slots):
    appointment_general_settings = get_appointment_general()

    #  first check that the current slot has availability
    enough_availability = available_slots[slot_dateTime] > 0

    #  how many more slots are needed and what is the datetime of the next slot?
    additional_slots_required = number_of_requested_slots - 1
    next_slot_dateTime = slot_dateTime + relativedelta(minutes=appointment_general_settings["slotUnit"])

    #  while more slots are required and availability is guaranteed so far
    while enough_availability and additional_slots_required > 0:
        #  does the next slot have availability too?
        #  (if the next slot datetime is not in the dictionary, return False. This happens when the incrementing
        #  pushes past the opening times)
        enough_availability = enough_availability and available_slots.get(next_slot_dateTime, False) > 0
        #  if there is not enough availability, break the loop
        if not enough_availability:
            break
        #  decrements the number of additional slots required and increment the slot datetime
        additional_slots_required -= 1
        next_slot_dateTime += relativedelta(minutes=appointment_general_settings["slotUnit"])

    return enough_availability



#  this function returns a dictionary with each key being one day and each value being a list of available time slots
#  that day for the requested appointment type
def get_available_time_slots(appointment_type_str: str):
    appointment_general_settings = get_appointment_general()
    #  get the number of available slots per timeslot
    available_slots = get_number_of_available_slots()
    appointment_type = find_appointment_type_one(appointment_type_str)

    #  how many slots does the requested appointment need
    number_of_requested_slots = ceil(appointment_type["duration"] / appointment_general_settings["slotUnit"])

    #  hold the available appointment start times per date
    available_appointments = {}

    #  iterate over the potential slot datetimes
    for slot_dateTime in available_slots.keys():
        #  check if enough of the following slots have availability
        #  enough means that if the desired appointment takes 4 slots, we need to make sure that the current slot and 3
        #  following slots all have availability

        enough_availability = can_appointment_be_on_slot(available_slots, slot_dateTime, number_of_requested_slots)

        if enough_availability:
            slot_date = slot_dateTime.date()
            if slot_date not in available_appointments:
                available_appointments[slot_date] = []
            available_appointments[slot_date].append("{:02d}:{:02d}".format(slot_dateTime.hour, slot_dateTime.minute))


    return available_appointments


def get_all_appointments():
    appointments_collection = _get_collection("appointments")

    today = datetime.today()

    all_appointments = [appointment for appointment in appointments_collection.find()]

    return all_appointments


def get_all_appointments_for_day(date: datetime.date):
    appointments_collection = _get_collection("appointments")

    lower_bound = datetime(year=date.year, month=date.month, day=date.day)
    upper_bound = datetime(year=date.year, month=date.month, day=date.day, hour=23, minute=59)

    all_appointments = [appointment for appointment in appointments_collection.find(
        {
            "$and": [
                {"startDateTime": {"$gte": lower_bound}},
                {"startDateTime": {"$lte": upper_bound}}
            ]
        }
    )]

    return all_appointments


def confirm_appointment_one(appointment_id: ObjectId):
    appointments_collection = _get_collection("appointments")

    return appointments_collection.update_one({"_id": appointment_id}, {"$set": {"appointmentConfirmed": True}}).acknowledged

def cancel_appointment_one(appointment_id: ObjectId):
    appointments_collection = _get_collection("appointments")

    return appointments_collection.update_one({"_id": appointment_id}, {"$set": {"appointmentConfirmed": False, "cancelled": True}}).acknowledged

def add_workshop_day(date: datetime.date):
    workshop_days_collection = _get_collection("workshopdays")

    workshopDayDateTime = datetime(date.year, date.month, date.day, 0, 0, 0)

    if workshop_days_collection.find_one({"date": workshopDayDateTime}) is None:
        success = workshop_days_collection.insert_one({"date": workshopDayDateTime}).acknowledged
    else:
        success = False

    return success

def get_workshop_days():
    workshopdays_collection = _get_collection("workshopdays")

    return [workshopday["date"].date() for workshopday in workshopdays_collection.find({})]

def is_workshopday(query_date: datetime.date):
    workshopdays_collection = _get_collection("workshopdays")

    query_datetime = datetime(query_date.year, query_date.month, query_date.day, 0, 0, 0)

    return workshopdays_collection.find_one({"date": query_datetime}) is not None

def delete_workshop_day(query_date: datetime.date):
    workshopdays_collection = _get_collection("workshopdays")

    query_datetime = datetime(query_date.year, query_date.month, query_date.day, 0, 0, 0)

    return workshopdays_collection.delete_one({"date": query_datetime}).deleted_count


def find_appointment_type_one(short: str):
    appointment_types_collection = _get_collection("appointmentTypes")
    return appointment_types_collection.find_one({"short": short})

def add_appointment_type(short: str, title:str, description: str, duration: int, active:bool):
    appointment_types_collection = _get_collection("appointmentTypes")
    if find_appointment_type_one(short) is not None:
        return False

    return appointment_types_collection.insert_one({
        "short": short,
        "title": title,
        "description": description,
        "duration": duration,
        "active": active
    }).acknowledged

def update_appointment_type(short: str, title:str, description: str, duration: int, active:bool):
    appointment_types_collection = _get_collection("appointmentTypes")
    if find_appointment_type_one(short) is None:
        return False

    return appointment_types_collection.update_one({"short": short}, {"$set": {
        "title": title,
        "description": description,
        "duration": duration,
        "active": active
    }}).acknowledged

def get_all_appointment_types():
    appointment_types_collection = _get_collection("appointmentTypes")
    return [a_t for a_t in appointment_types_collection.find({})]

def get_appointment_general():
    appointment_general_collection = _get_collection("appointmentGeneral")
    return appointment_general_collection.find_one({})

def set_appointment_general(**appoinment_general_data):
    appointment_general_collection = _get_collection("appointmentGeneral")
    return appointment_general_collection.update_one({}, {"$set": appoinment_general_data}).acknowledged

def get_appointment_concurrency_entries():
    appointment_concurrency_collection = _get_collection("appointmentConcurrency")
    return sorted([concurrencyEntry(ace["_id"], ace["afterTime"], ace["limit"]) for ace in appointment_concurrency_collection.find({})], key=lambda e: e.afterTime)

def update_appointment_concurrency_entries(concurrency_entries):
    appointment_concurrency_collection = _get_collection("appointmentConcurrency")
    success = True
    for concurrency_entry in concurrency_entries:
        entry_filter, entry_data = concurrency_entry.get_mongodb_filter_and_data()
        success &= appointment_concurrency_collection.update_one(entry_filter, {"$set": entry_data}).acknowledged

    return success

def add_appointment_concurrency_entry(entry: concurrencyEntry):
    appointment_concurrency_collection = _get_collection("appointmentConcurrency")
    _, entry_data = entry.get_mongodb_filter_and_data()
    return appointment_concurrency_collection.insert_one(entry_data).acknowledged

def remove_appointment_concurrency_entry(id: ObjectId):
    appointment_concurrency_collection = _get_collection("appointmentConcurrency")
    return appointment_concurrency_collection.delete_one({"_id": id}).acknowledged


def verify_user_pin(username: str, pin_to_verify: str):
    users_collection = _get_collection("users")
    user = users_collection.find_one({"username": username})
    if user is None:
        return False
    if "pin" not in user:
        return False
    return user["pin"] == pin_to_verify

def set_user_pin(username: str, pin: str):
    users_collection = _get_collection("users")
    return users_collection.update_one({"username": username}, {"$set": {"pin": pin}}).acknowledged