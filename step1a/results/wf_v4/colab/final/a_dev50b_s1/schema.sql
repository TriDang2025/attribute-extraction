CREATE TABLE "train_booking" (
  "train_booking_id" INTEGER,
  "train booking id" INTEGER,
  "payment location" TEXT,
  "travel time" INTERVAL,
  "arrival station" TEXT,
  "reference number" INTEGER,
  "number of tickets" INTEGER,
  "departure station" TEXT,
  "train id" INTEGER,
  "departure time" TIME,
  "arrival time" TIME,
  "total fee" NUMERIC(10, 2),
  "departure day" TEXT,
  PRIMARY KEY ("train booking id")
);

CREATE TABLE "hotel_booking" (
  "hotel_booking_id" INTEGER,
  "hotel booking id" INTEGER,
  "amenities" TEXT,
  "generic accommodation type" TEXT,
  "price adjective" TEXT,
  "postcode" INTEGER,
  "number of people" INTEGER,
  "address" TEXT,
  "location" TEXT,
  "hotel name" TEXT,
  "number of options" INTEGER,
  "start date" TEXT,
  "phone number" INTEGER,
  "reference number" INTEGER,
  "number of nights" INTEGER,
  "specific guesthouse" TEXT,
  "stars" INTEGER,
  PRIMARY KEY ("hotel booking id")
);

CREATE TABLE "restaurant_booking" (
  "restaurant_booking_id" INTEGER,
  "restaurant booking id" INTEGER,
  "food type" TEXT,
  "number of people" INTEGER,
  "day of week" TEXT,
  "postcode" INTEGER,
  "restaurant name" TEXT,
  "reference number" INTEGER,
  "restaurant reservation time" TIME,
  "restaurant address" TEXT,
  "restaurant type" TEXT,
  "area" TEXT,
  PRIMARY KEY ("restaurant booking id")
);
