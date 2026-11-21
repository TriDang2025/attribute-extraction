CREATE TABLE "accommodation" (
  "reservation number key" INTEGER,
  "amenities" TEXT,
  "internet" TEXT,
  "num people" INTEGER,
  "num nights" INTEGER,
  "train id" INTEGER,
  "attribute" TEXT,
  "entity" TEXT,
  "parking" TEXT,
  "start date" TEXT,
  "phone number" INTEGER,
  "num days" INTEGER,
  "price range noun" TEXT,
  "area" TEXT,
  "hotel name" TEXT,
  "guest house name" TEXT,
  "party size" TEXT,
  "str" TEXT,
  "price" TEXT,
  "reservation number" INTEGER,
  PRIMARY KEY ("reservation number key")
);

CREATE TABLE "train_info" (
  "train id key" INTEGER,
  "time int" INTEGER,
  "time" TIME,
  "departure location" TEXT,
  "location abbr" TEXT,
  "departure station" TEXT,
  "currency" NUMERIC(10, 2),
  "day of week" TEXT,
  "train id" TIME,
  "location str" TEXT,
  "duration str" INTERVAL,
  "day of week str" TEXT,
  "location" TEXT,
  "total fee" TEXT,
  "reference number" INTEGER,
  "departure time" INTEGER,
  "price" NUMERIC(10, 2),
  "travel time" TEXT,
  "time str" TIME,
  "seating_capacity" INTEGER,
  "booking id" INTEGER,
  PRIMARY KEY ("train id key")
);

CREATE TABLE "food_establishment" (
  "name id" INTEGER,
  "address" INTEGER,
  "venue name" TEXT,
  "restaurant name" TEXT,
  "location str" TEXT,
  "price range" TEXT,
  "phone number" INTEGER,
  "day of week" TEXT,
  "time int" TIME,
  "location area" TEXT,
  "num" INTEGER,
  "str" INTEGER,
  "cuisine" TEXT,
  "price" TEXT,
  "entry fee" TEXT,
  "time str" INTEGER,
  "reservation time" INTERVAL,
  "entrance fee" NUMERIC(10, 2),
  PRIMARY KEY ("name id")
);

CREATE TABLE "address" (
  "reference number" INTEGER,
  "accommodation id" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("accommodation id") REFERENCES "accommodation" ("reservation number key")
);

CREATE TABLE "location" (
  "location key" INTEGER,
  "location" TEXT,
  "location type" TEXT,
  "food type" TEXT,
  "location (food_establishment:6)" TEXT,
  "street name" TEXT,
  "noun" TEXT,
  "postcode" INTEGER,
  "cinema name" TEXT,
  "attraction type" TEXT,
  "attraction name" TEXT,
  "location abbrev" TEXT,
  "favorite museum" TEXT,
  "bed and breakfast" TEXT,
  "location (address:8)" TEXT,
  "address" TEXT,
  "location str" TEXT,
  "attraction name (location:1)" TEXT,
  PRIMARY KEY ("location key")
);
