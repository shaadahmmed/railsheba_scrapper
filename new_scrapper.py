import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from os import environ
import webbrowser


def reserve_seat(ticket_id, trip_route_id, headers):
    print(f"Trying to book {ticket_id}")
    seat_book_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/reserve-seat"
    res = requests.patch(
        seat_book_url,
        json={
            "ticket_id": ticket_id,
            "route_id": trip_route_id,
        },
        headers=headers,
    )
    res_dict = res.json()
    if res_dict.get("error"):
        print(res_dict["error"]["messages"])
        return False
    return True


def release_seat(ticket_id, trip_route_id, headers):
    print("Trying to relase seat", ticket_id)
    seat_release_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/release-seat"
    res = requests.patch(
        seat_release_url,
        json={"ticket_id": ticket_id, "route_id": trip_route_id},
        headers=headers,
    )
    res_dict = res.json()
    if res_dict.get("error"):
        print(res_dict["error"]["messages"])
        return False
    print("Seat Released!")
    return True


def login():
    # profile_url = "https://railspaapi.shohoz.com/v1.0/web/auth/profile"
    login_url = "https://railspaapi.shohoz.com/v1.0/web/auth/sign-in"
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    login_payload = {
        "mobile_number": environ.get("MOBILE_NUMBER"),
        "password": environ.get("PASSWORD"),
    }
    login_response = session.post(login_url, data=login_payload, headers=headers)
    login_dict = login_response.json()
    auth_token = ""
    if "data" in login_dict:
        print("Login successful!")
        print("Session Started")
        auth_token = login_dict["data"]["token"]
        # auth_hash = login_dict["extra"]["hash"]
        headers["Authorization"] = f"Bearer {auth_token}"
        return session, headers
    else:
        print(login_dict["error"]["messages"])
        exit()


def wait_time():
    start_time = datetime.now().replace(
        hour=int(environ.get("START_HOUR")),
        minute=int(environ.get("START_MINUTE")),
        second=0,
        microsecond=0,
    )
    print("Waiting for the target time...")
    current_time = datetime.now()
    time_to_wait = (start_time - current_time).total_seconds()
    if time_to_wait < 0:
        print("Time has already passed!")
    else:
        time.sleep(time_to_wait)


def search_train(headers):
    from_station = environ.get("FROM_STATION")
    to_station = environ.get("TO_STATION")
    date_of_journey = environ.get("DATE")
    seat_class = environ.get("SEAT_CLASS")
    train_search_url = f"https://railspaapi.shohoz.com/v1.0/web/bookings/search-trips-v2?from_city={from_station}&to_city={to_station}&date_of_journey={date_of_journey}&seat_class={seat_class}"

    train_search_dict = None
    while True:
        print("Searching for the trains...")
        train_search_response = requests.get(train_search_url, headers=headers)
        train_search_dict = train_search_response.json()
        if train_search_dict["data"]["trains"]:
            break
    print("Trains Found!")
    return train_search_dict


def check_seat_availability(headers):
    trip_number = environ.get("TRAIN_NAME")
    seat_class = environ.get("SEAT_CLASS")
    number_of_seats = int(environ.get("NUMBER_OF_PASSENGERS"))

    count = 0
    trip_id = ""
    trip_route_id = ""
    boarding_point_id = ""
    while not trip_id and count < 100:
        count += 1
        train_search_dict = search_train(headers)
        print("Finding Desired Train...")
        for train in train_search_dict["data"]["trains"]:
            if trip_number.upper() in train["trip_number"]:
                train_found = True
                print(train["trip_number"], "Found!")
                print("Checking for the seat availability...")
                for seat_type in train["seat_types"]:
                    if seat_type["type"] == seat_class:
                        seat_counts = (
                            seat_type["seat_counts"]["online"]
                            + seat_type["seat_counts"]["offline"]
                        )
                        if seat_counts < number_of_seats:
                            # time.sleep(0.5)
                            print("Try No: ", count)
                            continue
                        else:
                            print("Seat Available!")
                            print("Seat Count: ", seat_counts)
                            trip_id = seat_type["trip_id"]
                            # route_id = seat_type["route_id"]
                            trip_route_id = seat_type["trip_route_id"]
                            boarding_point_id = train["boarding_points"][0][
                                "trip_point_id"
                            ]
                            return (
                                trip_id,
                                trip_route_id,
                                boarding_point_id,
                                number_of_seats,
                            )
    if not train_found:
        print("Check your train name")
        print("Train day off or the train is not available!")
        exit()
    if trip_id == "":
        print("No Seat Available for the selected train!")
        exit()


def seat_search(trip_id, trip_route_id, headers):
    train_seat_url = f"https://railspaapi.shohoz.com/v1.0/web/bookings/seat-layout?trip_id={trip_id}&trip_route_id={trip_route_id}"
    train_seat_response = requests.get(train_seat_url, headers=headers)
    train_seat_dict = train_seat_response.json()
    if train_seat_dict.get("error"):
        print(train_seat_dict["error"]["messages"])
        print("Try another account")
        exit()
    seat_layout = train_seat_dict["data"]["seatLayout"]
    return seat_layout


def any_seat_booking(seat_layout, trip_id, trip_route_id, number_of_seats, headers):
    is_window_seat = eval(environ.get("WINDOW_SEAT"))
    seats_dict = {
        "trip_id": trip_id,
        "trip_route_id": trip_route_id,
        "ticket_ids": [],
    }
    count = 0
    for room in seat_layout:
        if room["seat_availability"]:
            room_layout = None
            if eval(environ.get("UP_TRAIN")):
                room_layout = room["layout"][::-1]
            else:
                room_layout = room["layout"]
            for row in room_layout:
                if is_window_seat and number_of_seats == 1:
                    print("Trying to book window seat...")
                    window_1 = row[0]
                    window_2 = row[-1]
                    if window_1["seat_availability"]:
                        if reserve_seat(window_1["ticket_id"], trip_route_id, headers):
                            seats_dict["ticket_ids"].append(window_1["ticket_id"])
                            print("Window Seat Reserved!", window_1["seat_number"])
                            return seats_dict, True
                    if window_2["seat_availability"]:
                        if reserve_seat(window_2["ticket_id"], trip_route_id, headers):
                            seats_dict["ticket_ids"].append(window_2["ticket_id"])
                            print("Window Seat Reserved!", window_2["seat_number"])
                            return seats_dict, True
                else:
                    for seat in row:
                        if seat["seat_availability"]:
                            # release_seat(seat["ticket_id"], trip_route_id, headers)
                            # continue
                            if not reserve_seat(
                                seat["ticket_id"], trip_route_id, headers
                            ):
                                continue
                            count += 1
                            seats_dict["ticket_ids"].append(seat["ticket_id"])
                            print("Seat Reserved!", seat["seat_number"])
                            if count == number_of_seats:
                                return seats_dict, True

    return seats_dict, False


def same_row_seat(seat_layout, trip_id, trip_route_id, number_of_seats, headers):
    seats_dict = {
        "trip_id": trip_id,
        "trip_route_id": trip_route_id,
        "ticket_ids": [],
    }
    count = 0
    for room in seat_layout:
        if room["seat_availability"]:
            room_layout = None
            if eval(environ.get("UP_TRAIN")):
                room_layout = room["layout"][::-1]
            else:
                room_layout = room["layout"]
            for row in room_layout:
                left = []
                right = []
                isLeft = True
                for seat in row:
                    if seat["seat_availability"]:
                        if seat["seat_number"] == "":
                            isLeft = False
                            continue
                        if isLeft:
                            left.append(seat)
                        else:
                            right.append(seat)

                if len(left) >= number_of_seats:
                    count = 0
                    for seat in left:
                        if not reserve_seat(seat["ticket_id"], trip_route_id, headers):
                            left.remove(seat)
                            continue
                        count += 1
                        seats_dict["ticket_ids"].append(seat["ticket_id"])
                        print("Seat Reserved!", seat["seat_number"])
                        # print(seat)
                        if count == number_of_seats:
                            return seats_dict, True

                elif len(right) >= number_of_seats:
                    count = 0
                    for seat in right:
                        if not reserve_seat(seat["ticket_id"], trip_route_id, headers):
                            right.remove(seat)
                            continue
                        count += 1
                        seats_dict["ticket_ids"].append(seat["ticket_id"])
                        print("Seat Reserved!", seat["seat_number"])
                        # print(seat)
                        if count == number_of_seats:
                            return seats_dict, True

    return seats_dict, False


def send_otp(session, seats_dict, headers):
    passengers_details_url = (
        "https://railspaapi.shohoz.com/v1.0/web/bookings/passenger-details"
    )
    # post request
    before_otp_response = session.post(
        passengers_details_url, json=seats_dict, headers=headers
    )
    before_otp_dict = before_otp_response.json()
    print(before_otp_dict)

    if before_otp_dict.get("error"):
        print(before_otp_dict["error"]["messages"])
        exit()


def scrapper():
    load_dotenv(dotenv_path=".env", override=True)
    session, headers = login()
    wait_time()

    seat_reserved = False
    while not seat_reserved:
        trip_id, trip_route_id, boarding_point_id, number_of_seats = (
            check_seat_availability(headers)
        )
        seat_layout = seat_search(trip_id, trip_route_id, headers)
        is_any_seat = eval(environ.get("ANY_SEAT"))
        if not is_any_seat and number_of_seats > 1:
            seats_dict, seat_reserved = same_row_seat(
                seat_layout, trip_id, trip_route_id, number_of_seats, headers
            )
        if not seat_reserved:
            seats_dict, seat_reserved = any_seat_booking(
                seat_layout, trip_id, trip_route_id, number_of_seats, headers
            )

        if not seat_reserved:
            print("No available seats!")
            print("Trying again from the begining...")

    send_otp(session, seats_dict, headers)

    otp = input("Enter OTP: ")
    seats_dict["otp"] = otp
    otp_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/verify-otp"
    after_opt_verification = session.post(otp_url, json=seats_dict, headers=headers)
    print(after_opt_verification.json())

    go_to_payment_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/confirm"
    none_list = [None for i in range(number_of_seats)]
    blank_list = ["" for i in range(number_of_seats)]
    payment_dict = {
        "is_bkash_online": True,
        "boarding_point_id": boarding_point_id,
        "contactperson": 0,
        "from_city": environ.get("FROM_STATION"),
        "to_city": environ.get("TO_STATION"),
        "date_of_journey": environ.get("DATE"),
        "seat_class": environ.get("SEAT_CLASS"),
        "gender": eval(environ.get("GENDER")),
        "page": blank_list,
        "passengerType": eval(environ.get("PASSENGER_TYPE")),
        "pemail": environ.get("EMAIL"),
        "pmobile": environ.get("MOBILE_NUMBER"),
        "pname": eval(environ.get("PASSENGER_NAME")),
        "ppassport": blank_list,
        "priyojon_order_id": None,
        "referral_mobile_number": None,
        "ticket_ids": seats_dict["ticket_ids"],
        "trip_id": trip_id,
        "trip_route_id": trip_route_id,
        "isShohoz": 0,
        "enable_sms_alert": 0,
        "first_name": none_list,
        "middle_name": none_list,
        "last_name": none_list,
        "date_of_birth": none_list,
        "nationality": none_list,
        "passport_type": none_list,
        "passport_no": none_list,
        "passport_expiry_date": none_list,
        "visa_type": none_list,
        "visa_no": none_list,
        "visa_issue_place": none_list,
        "visa_issue_date": none_list,
        "visa_expire_date": none_list,
        "otp": otp,
        "selected_mobile_transaction": 1,
    }

    before_payment_response = session.patch(
        go_to_payment_url, json=payment_dict, headers=headers
    )
    print(before_payment_response.json())
    before_payment_dict = before_payment_response.json()
    redirect_url = before_payment_dict["data"]["redirectUrl"]
    webbrowser.open(redirect_url)


scrapper()
