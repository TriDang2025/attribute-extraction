CREATE TABLE "train" (
  "arrival location" TEXT,
  "arrival time" TIME,
  "departure location" TEXT,
  "departure time" TIME,
  "destination city" TEXT,
  "price per ticket" NUMERIC(10, 2),
  "travel time" INTERVAL,
  "train id" INTEGER,
  PRIMARY KEY ("train id")
);

CREATE TABLE "train_booking" (
  "number of tickets" INTEGER,
  "total fee" NUMERIC(10, 2),
  "travel date" TEXT,
  "train id" INTEGER,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("train id") REFERENCES "train" ("train id")
);

CREATE TABLE "hotel" (
  "hotel address" TEXT,
  "hotel location" TEXT,
  "hotel phone number" TEXT,
  "hotel type" TEXT,
  "location" TEXT,
  "location description" TEXT,
  "postcode" INTEGER,
  "price adjective" TEXT,
  "price extreme" TEXT,
  "price range" TEXT,
  "specific hotel name" TEXT,
  "star rating" INTEGER,
  "hotel name" TEXT,
  PRIMARY KEY ("hotel name")
);

CREATE TABLE "hotel_booking" (
  "hotel number of guests" INTEGER,
  "hotel number of nights" INTEGER,
  "start date" TEXT,
  "hotel name" INTEGER,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("hotel name") REFERENCES "hotel" ("hotel name")
);

CREATE TABLE "restaurant" (
  "postcode" INTEGER,
  "price range" TEXT,
  "restaurant address" TEXT,
  "restaurant area" TEXT,
  "restaurant food type" TEXT,
  "restaurant location" TEXT,
  "restaurant phone number" TEXT,
  "taxi phone numbers" TEXT,
  "restaurant name" TEXT,
  PRIMARY KEY ("restaurant name")
);

CREATE TABLE "restaurant_booking" (
  "number of options" INTEGER,
  "number of people" INTEGER,
  "reservation date" TEXT,
  "reservation time" TIME,
  "restaurant name" INTEGER,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("restaurant name") REFERENCES "restaurant" ("restaurant name")
);
