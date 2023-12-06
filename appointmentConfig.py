from datetime import time


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
