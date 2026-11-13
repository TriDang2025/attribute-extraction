CREATE TABLE "train_id" (
  "train id key" INTEGER,
  "train id" INTEGER,
  "reference number" INTEGER,
  "reference number (restaurant:8)" INTEGER,
  PRIMARY KEY ("train id key")
);

CREATE TABLE "train_departure_time" (
  "departure location" TEXT,
  "departure time" TIME,
  "time query" TEXT,
  "reservation time" TIME,
  "time for taxi" TIME,
  PRIMARY KEY ("departure location"),
  FOREIGN KEY ("departure location") REFERENCES "train_id" ("train id key")
);

CREATE TABLE "train_arrival_time" (
  "arrival location key" INTEGER,
  "arrival location" TEXT,
  "arrival time" TIME,
  "destination city" TEXT,
  "restaurant phone number" TEXT,
  "restaurant address" TEXT,
  "restaurant food type" TEXT,
  "postcode" INTEGER,
  "taxi phone numbers" INTEGER,
  "restaurant name" TEXT,
  "restaurant location" TEXT,
  PRIMARY KEY ("arrival location key")
);

CREATE TABLE "train_price_per_ticket" (
  "train_price_per_ticket id" INTEGER,
  "price per ticket" NUMERIC(10, 2),
  PRIMARY KEY ("train_price_per_ticket id")
);

CREATE TABLE "train_number_of_trains" (
  "train_number" INTEGER,
  "number of trains" INTEGER,
  "number of results" INTEGER,
  PRIMARY KEY ("train_number")
);

CREATE TABLE "train_travel_date" (
  "travel date key" INTEGER,
  "travel date" TEXT,
  "travel time" INTERVAL,
  "start date" TEXT,
  "reservation date" TEXT,
  PRIMARY KEY ("travel date key")
);

CREATE TABLE "train_number_of_tickets" (
  "train_number" INTEGER,
  "number of tickets" INTEGER,
  "number of people" INTEGER,
  PRIMARY KEY ("train_number")
);

CREATE TABLE "train_total_fee" (
  "train_total_fee" INTEGER,
  "total fee" NUMERIC(10, 2),
  PRIMARY KEY ("train_total_fee")
);
