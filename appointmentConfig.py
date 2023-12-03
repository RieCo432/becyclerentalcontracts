from datetime import time

# TODO: this should all be moved to separate collections in the database
appointment_shorts = [
    "rent",
    "xsrep",
    "srep",
    "mrep",
    "lrep",
    "xlrep",
    "other"
]
appointment_titles = {
    "rent": "Bike Rental",
    "xsrep": "Minuscule Repair",
    "srep": "Small Repair",
    "mrep": "Medium Repair",
    "lrep": "Large Repair",
    "xlrep": "Massive Repair",
    "other": "Other"
}
appointment_descs = {
    "rent": "Rent a bike (2h00)",
    "xsrep": "Fix a flat, swap breakpads or chains (0h15)",
    "srep": "Adjust brakes or gears. (0h30)",
    "mrep": "Adjust brakes and gears. (1h00)",
    "lrep": "All of the above (1h30)",
    "xlrep": "Complete Service (2h00)",
    "other": "Returns, questions, bring us donations, etc. (0h15) Booking an appointment for these services is not necessary."
}
appointment_durations = {
    "rent": 120,
    "xsrep": 15,
    "srep": 30,
    "mrep": 60,
    "lrep": 90,
    "xlrep": 120,
    "other": 15
}

appointment_slotUnit = 15

appointment_openingDays = [0, 2]  # Monday and Wednesday

# How many appointments are allowed to happen at given times?
# Note, this is not how many appointents are allowed to start at a given time, but how many can be starting or ongoing
# For each time that is not specified, the value from the previous specified slot will be taken
# i.e. when specifying that 2 appointments at 5pm are allowed and  4 appointments at 6pm, only 2 are allowed at 5:30pm
# It is wise to start with a low number shortly after opening, then slowly increase until peak time. After that, it is
# a good idea to specify a wind-down period to make sure appointments have to be wrapped up as closing time approaches
# This effectively serves as a way of defining opening hours, as any time before 4:15pm will be disallowed due to
# 0 appointments being allowed after 12:00am and 0 appointments after 7:45pm
appointment_concurrency = {
    time(0,0): 0,
    time(16, 15): 2,
    time(17, 0): 4,
    time(18, 0): 6,
    time(19, 15): 2,
    time(19, 45): 0
}

# # set a limit on how many appointments of some type are allowed per day
# appointment_typeLimits = {
#     "rent": 4
# }
