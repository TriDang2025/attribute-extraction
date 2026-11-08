CREATE TABLE "train_journey" (
  "arrival station" TEXT,
  "arrival time" TIME,
  "departure day" TEXT,
  "departure station" TEXT,
  "departure time" TIME,
  "train id" INTEGER,
  "travel time" INTERVAL,
  PRIMARY KEY ("train id")
);

CREATE TABLE "train_booking" (
  "number of tickets" INTEGER,
  "payment location" TEXT,
  "reference number" INTEGER,
  "total fee" NUMERIC(10, 2),
  "train id" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("train id") REFERENCES "train_journey" ("train id")
);

CREATE TABLE "hotel" (
  "accommodation type" TEXT,
  "address" TEXT,
  "amenities" TEXT,
  "generic accommodation type" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "phone number" INTEGER,
  "postcode" INTEGER,
  "price adjective" TEXT,
  "specific guesthouse" TEXT,
  "stars" INTEGER,
  PRIMARY KEY ("hotel name")
);

CREATE TABLE "hotel_reservation" (
  "number of nights" INTEGER,
  "number of people" INTEGER,
  "reference number" INTEGER,
  "start date" TEXT,
  "hotel name" TEXT,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("hotel name") REFERENCES "hotel" ("hotel name")
);

CREATE TABLE "restaurant" (
  "area" TEXT,
  "food type" TEXT,
  "postcode" INTEGER,
  "price range confirmation" TEXT,
  "price range question" TEXT,
  "restaurant address" TEXT,
  "restaurant name" TEXT,
  "restaurant phone number" INTEGER,
  "restaurant postcode" TEXT,
  "restaurant type" TEXT,
  "specific address" TEXT,
  PRIMARY KEY ("restaurant name")
);

CREATE TABLE "restaurant_reservation" (
  "day of week" TEXT,
  "number of people" INTEGER,
  "reference number" INTEGER,
  "restaurant reference number" INTEGER,
  "restaurant reservation time" TIME,
  "restaurant name" TEXT,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("restaurant name") REFERENCES "restaurant" ("restaurant name")
);
