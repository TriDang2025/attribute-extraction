CREATE TABLE "train_journey" (
  "train_journey_id" INTEGER,
  "train journey id" INTEGER,
  "arrival station" TEXT,
  "arrival time" TIME,
  "departure day" TEXT,
  "departure station" TEXT,
  "departure time" TIME,
  "train id" INTEGER,
  "travel time" INTERVAL,
  PRIMARY KEY ("train journey id")
);

CREATE TABLE "hotel_booking" (
  "hotel_booking_id" INTEGER,
  "hotel booking id" INTEGER,
  "generic accommodation type" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "number of people" INTEGER,
  "phone number" INTEGER,
  "postcode" INTEGER,
  "price adjective" TEXT,
  "reference number" INTEGER,
  "restaurant name" TEXT,
  "specific guesthouse" TEXT,
  "stars" INTEGER,
  "start date" TEXT,
  PRIMARY KEY ("hotel booking id")
);

CREATE TABLE "restaurant_booking" (
  "restaurant_booking_id" INTEGER,
  "restaurant booking id" INTEGER,
  "area" TEXT,
  "day of week" TEXT,
  "food type" TEXT,
  "number of people" INTEGER,
  "postcode" INTEGER,
  "price range confirmation" TEXT,
  "price range question" TEXT,
  "reference number" INTEGER,
  "reservation duration" INTERVAL,
  "restaurant address" TEXT,
  "restaurant name" TEXT,
  "restaurant phone number" INTEGER,
  "restaurant postcode" TEXT,
  "restaurant reservation time" TIME,
  "restaurant type" TEXT,
  "specific address" TEXT,
  PRIMARY KEY ("restaurant booking id")
);
