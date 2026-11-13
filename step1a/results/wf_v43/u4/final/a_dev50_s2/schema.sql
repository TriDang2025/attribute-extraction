CREATE TABLE "train_id" (
  "train id" INTEGER,
  PRIMARY KEY ("train id")
);

CREATE TABLE "train_departure_time" (
  "departure time" TIME,
  "departure location" TEXT,
  PRIMARY KEY ("departure time"),
  FOREIGN KEY ("departure location") REFERENCES "train_id" ("train id")
);

CREATE TABLE "train_arrival_time" (
  "description" INTEGER,
  "destination city" TEXT,
  "stay duration days" INTEGER,
  "travel date" TEXT,
  "travel time" INTERVAL,
  "arrival time" TIME,
  PRIMARY KEY ("description")
);

CREATE TABLE "train_price_per_ticket" (
  "train_price_per_ticket id" INTEGER,
  "price per ticket" NUMERIC(10, 2),
  PRIMARY KEY ("train_price_per_ticket id")
);

CREATE TABLE "train_number_of_tickets" (
  "train_number_of_tickets" INTEGER,
  "number of tickets" INTEGER,
  PRIMARY KEY ("train_number_of_tickets")
);

CREATE TABLE "train_number_of_trains" (
  "train_number_of_trains" INTEGER,
  "number of trains" INTEGER,
  PRIMARY KEY ("train_number_of_trains")
);

CREATE TABLE "train_total_fee" (
  "train_total_fee" INTEGER,
  "total fee" NUMERIC(10, 2),
  PRIMARY KEY ("train_total_fee")
);

CREATE TABLE "train_reference_number" (
  "reference number key" INTEGER,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number key")
);
