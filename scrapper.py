import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import os
import webbrowser

login_url = "https://railspaapi.shohoz.com/v1.0/web/auth/sign-in"


def book_seat(json, headers):
    print(json)
    seat_book_url = "https://railspaapi.shohoz.com/v1.0/web/bookings/reserve-seat"
    res = requests.patch(seat_book_url, json=json, headers=headers)
    res_dict = res.json()
    if res_dict.get("error"):
        return False
    return True


def scrapper():
    load_dotenv(dotenv_path=".env", override=True)
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    login_payload = {
        "mobile_number": os.getenv("MOBILE_NUMBER"),
        "password": os.getenv("PASSWORD"),
    }
    login_response = session.post(login_url, data=login_payload, headers=headers)
    login_dict = login_response.json()
    auth_token = ""
    # auth_hash = ""
    # print(login_dict)
    if "data" in login_dict:
        print("Login successful!")
        print("Session Started")
        auth_token = login_dict["data"]["token"]
        # auth_hash = login_dict["extra"]["hash"]
        headers["Authorization"] = f"Bearer {auth_token}"
    else:
        print(login_dict["error"]["messages"])
        exit()
    start_time = datetime.now().replace(
        hour=int(os.getenv("START_HOUR")),
        minute=int(os.getenv("START_MINUTE")),
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
    from_station = os.getenv("FROM_STATION")
    to_station = os.getenv("TO_STATION")
    date_of_journey = os.getenv("DATE")
    seat_class = os.getenv("SEAT_CLASS")
    trip_number = os.getenv("TRAIN_NAME")
    number_of_seats = int(os.getenv("NUMBER_OF_PASSENGERS"))
    train_search_url = f"https://railspaapi.shohoz.com/v1.0/web/bookings/search-trips-v2?from_city={from_station}&to_city={to_station}&date_of_journey={date_of_journey}&seat_class={seat_class}"
    train_search_response = requests.get(train_search_url, headers=headers)
    train_search_dict = train_search_response.json()
    trip_id = ""
    # route_id = ""
    trip_route_id = ""
    boarding_point_id = ""

    for train in train_search_dict["data"]["trains"]:
        if train["trip_number"] == trip_number:
            for seat_type in train["seat_types"]:
                if seat_type["type"] == seat_class:
                    seat_counts = (
                        seat_type["seat_counts"]["online"]
                        + seat_type["seat_counts"]["offline"]
                    )
                    if seat_counts < number_of_seats:
                        continue
                    else:
                        print("Seat Available!")
                        print("Seat Count: ", seat_counts)
                        trip_id = seat_type["trip_id"]
                        # route_id = seat_type["route_id"]
                        trip_route_id = seat_type["trip_route_id"]
                        break

            boarding_point_id = train["boarding_points"][0]["trip_point_id"]
            break

    if trip_id == "":
        print("No Seat Available for the selected train!")
        exit()

    train_seat_url = f"https://railspaapi.shohoz.com/v1.0/web/bookings/seat-layout?trip_id={trip_id}&trip_route_id={trip_route_id}"
    train_seat_response = requests.get(train_seat_url, headers=headers)
    train_seat_dict = train_seat_response.json()
    # print(train_seat_dict)
    seat_layout = train_seat_dict["data"]["seatLayout"]
    desired_seats = eval(os.getenv("DESIRED_SEATS"))
    desired_seats_from_train = []

    seats_dict = {
        "trip_id": trip_id,
        "trip_route_id": trip_route_id,
        "ticket_ids": [],
    }

    available_rooms = {}
    seat_reserved = False

    for room in seat_layout:
        if room["seat_availability"]:
            available_rooms[room["floor_name"]] = []
            for row in room["layout"]:
                left = []
                right = []
                isLeft = True
                for seat in row:
                    if len(desired_seats_from_train) == number_of_seats:
                        break
                    if seat["seat_number"] in desired_seats:
                        desired_seats_from_train.append(seat)
                    if seat["seat_number"] == "":
                        isLeft = False
                    if seat["seat_availability"]:
                        if isLeft:
                            left.append(seat)
                        else:
                            right.append(seat)
                        available_rooms[room["floor_name"]].append(seat)

                if len(desired_seats_from_train) == number_of_seats:
                    for seat in desired_seats_from_train:
                        if not book_seat(
                            {
                                "ticket_id": seat["ticket_id"],
                                "route_id": trip_route_id,
                            },
                            headers,
                        ):
                            continue
                        print(seat)
                        seats_dict["ticket_ids"].append(seat["ticket_id"])
                    seat_reserved = True
                    break
                elif len(left) >= number_of_seats:
                    count = 0
                    for seat in left:
                        if not book_seat(
                            {
                                "ticket_id": seat["ticket_id"],
                                "route_id": trip_route_id,
                            },
                            headers,
                        ):
                            continue
                        seats_dict["ticket_ids"].append(seat["ticket_id"])
                        print(seat)
                        count += 1
                        if count == number_of_seats:
                            break
                    seat_reserved = True
                    break
                elif len(right) >= number_of_seats:
                    count = 0
                    for seat in right:
                        if not book_seat(
                            {
                                "ticket_id": seat["ticket_id"],
                                "route_id": trip_route_id,
                            },
                            headers,
                        ):
                            continue
                        print(seat)
                        seats_dict["ticket_ids"].append(seat["ticket_id"])
                        count += 1
                        if count == number_of_seats:
                            break
                    seat_reserved = True
                    break

        if seat_reserved:
            break

    if not seat_reserved:
        for room in available_rooms:
            if len(room) >= number_of_seats:
                researved_count = 0
                for seat in room:
                    if not book_seat(
                        {
                            "ticket_id": seat["ticket_id"],
                            "route_id": trip_route_id,
                        },
                        headers,
                    ):
                        continue
                    print(seat)
                    seats_dict["ticket_ids"].append(seat["ticket_id"])
                    researved_count += 1
                    if researved_count == number_of_seats:
                        seat_reserved = True
                        break
            if seat_reserved:
                break

    if not seat_reserved:
        print("No available seats!")
        exit()

    # exit()

    # print(seats_dict["ticket_ids"])
    # exit()
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
        "from_city": from_station,
        "to_city": to_station,
        "date_of_journey": date_of_journey,
        "seat_class": seat_class,
        "gender": ["male" for i in range(number_of_seats)],
        "page": blank_list,
        "passengerType": ["Adult" for i in range(number_of_seats)],
        "pemail": os.getenv("EMAIL"),
        "pmobile": os.getenv("MOBILE_NUMBER"),
        "pname": eval(os.getenv("PASSENGER_NAME")),
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
