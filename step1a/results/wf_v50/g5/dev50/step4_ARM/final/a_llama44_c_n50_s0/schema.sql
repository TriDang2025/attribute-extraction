CREATE TABLE "accommodation" (
  "accommodation" INTEGER,
  "str" TEXT,
  "amenities" TEXT,
  "internet" TEXT,
  "parking" TEXT,
  PRIMARY KEY ("accommodation")
);

CREATE TABLE "train_info" (
  "id" INTEGER,
  "train id" INTEGER,
  "booking id" INTEGER,
  "currency" NUMERIC(10, 2),
  "departure day" TEXT,
  "departure day (train_info:4)" TEXT,
  "departure location" TEXT,
  "departure station" TEXT,
  "departure time" INTEGER,
  "duration str" INTERVAL,
  "location" TEXT,
  "location abbr" TEXT,
  "location str" TEXT,
  "location type" TEXT,
  "price" NUMERIC(10, 2),
  "reference number" INTEGER,
  "stansted airport" TEXT,
  "departure time (train_info:16)" TIME,
  "time int" INTEGER,
  "departure time (train_info:18)" TIME,
  "total fee" TEXT,
  "train id (train_info:20)" TIME,
  "travel time" TEXT,
  "seating_capacity" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "food_establishment" (
  "phone number key" INTEGER,
  "address" INTEGER,
  "cuisine" TEXT,
  "day of week" TEXT,
  "entry fee" TEXT,
  "food type" TEXT,
  "location" TEXT,
  "location area" TEXT,
  "location str" TEXT,
  "num" INTEGER,
  "phone number" INTEGER,
  "price" TEXT,
  PRIMARY KEY ("phone number key")
);

CREATE TABLE "location" (
  "reference number key" INTEGER,
  "attraction name" TEXT,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number key")
);
