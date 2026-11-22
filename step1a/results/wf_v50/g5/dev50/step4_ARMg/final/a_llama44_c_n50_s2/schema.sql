CREATE TABLE "accommodation" (
  "reservation number key" INTEGER,
  "price range" TEXT,
  "amenities" TEXT,
  "hotel name" TEXT,
  "price" TEXT,
  "price range noun" TEXT,
  "start date" TEXT,
  "party size" TEXT,
  "reservation number" INTEGER,
  "num nights" INTEGER,
  "parking" TEXT,
  "guest house name" TEXT,
  "num days" INTEGER,
  "entity" TEXT,
  "num people" INTEGER,
  "internet" TEXT,
  "attribute" TEXT,
  PRIMARY KEY ("reservation number key")
);

CREATE TABLE "train_info" (
  "booking id key" INTEGER,
  "train id" TIME,
  "location abbr" TEXT,
  "currency" NUMERIC(10, 2),
  "departure time" INTEGER,
  "departure time (train_info:16)" TIME,
  "departure location" TEXT,
  "location type" TEXT,
  "location" TEXT,
  "seating_capacity" INTEGER,
  "travel time" TEXT,
  "total fee" TEXT,
  "departure day" TEXT,
  "booking id" INTEGER,
  "departure day (train_info:4)" TEXT,
  "duration str" INTERVAL,
  "departure time (train_info:18)" TIME,
  "departure station" TEXT,
  "time int" INTEGER,
  "reference number" INTEGER,
  "price" NUMERIC(10, 2),
  "location str" TEXT,
  PRIMARY KEY ("booking id key")
);

CREATE TABLE "food_establishment" (
  "phone number key" INTEGER,
  "address" INTEGER,
  "cuisine" TEXT,
  "location" TEXT,
  "str" INTEGER,
  "food type" TEXT,
  "phone number" INTEGER,
  "price range" TEXT,
  "entry fee" TEXT,
  "num" INTEGER,
  "restaurant name" TEXT,
  "location area" TEXT,
  PRIMARY KEY ("phone number key")
);

CREATE TABLE "location" (
  "reference number key" INTEGER,
  "attraction name" TEXT,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "address" (
  "date" TEXT,
  "str" TEXT,
  "area" TEXT,
  "location" TEXT,
  "day of week" TEXT,
  "location str" TEXT,
  "reservation time" INTERVAL,
  "venue name" TEXT,
  "time str" INTEGER,
  "price" TEXT,
  "time int" TIME,
  "address" TEXT,
  "cinema name" TEXT,
  "favorite museum" TEXT,
  "attraction type" TEXT,
  "attraction name" TEXT,
  "postcode" INTEGER,
  "noun" TEXT,
  "street name" TEXT,
  "location abbrev" TEXT,
  "location str (address:10)" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "location (address:8)" TEXT,
  PRIMARY KEY ("area"),
  FOREIGN KEY ("location (address:8)") REFERENCES "location" ("reference number key")
);
