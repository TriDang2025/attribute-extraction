CREATE TABLE "accommodation" (
  "accommodation" INTEGER,
  "str" TEXT,
  "amenities" TEXT,
  "internet" TEXT,
  "parking" TEXT,
  PRIMARY KEY ("accommodation")
);

CREATE TABLE "train_info" (
  "train id key" INTEGER,
  "train id" INTEGER,
  "booking id" INTEGER,
  "currency" NUMERIC(10, 2),
  "day of week" TEXT,
  "day of week str" TEXT,
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
  "time" TIME,
  "time int" INTEGER,
  "time str" TIME,
  "train id (train_info:20)" TIME,
  "seating_capacity" INTEGER,
  PRIMARY KEY ("train id key")
);

CREATE TABLE "food_establishment" (
  "id" INTEGER,
  "attribute" TEXT,
  "entity" TEXT,
  "guest house name" TEXT,
  "hotel name" TEXT,
  "price" TEXT,
  "price range" TEXT,
  "price range noun" TEXT,
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
  "price (food_establishment:12)" TEXT,
  "price range (food_establishment:13)" TEXT,
  "restaurant name" TEXT,
  "str" INTEGER,
  "venue name" TEXT,
  "attraction name" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "address" (
  "address id" INTEGER,
  "area" TEXT,
  "location" TEXT,
  "address" TEXT,
  "attraction name" TEXT,
  "attraction type" TEXT,
  "bed and breakfast" TEXT,
  "cinema name" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "favorite museum" TEXT,
  "postcode" INTEGER,
  "street name" TEXT,
  "reference number" INTEGER,
  "food_establishment id" INTEGER,
  PRIMARY KEY ("address id"),
  FOREIGN KEY ("food_establishment id") REFERENCES "food_establishment" ("id")
);

CREATE TABLE "address_2" (
  "location key" INTEGER,
  "location" TEXT,
  "location abbrev" TEXT,
  "location str" TEXT,
  "noun" TEXT,
  PRIMARY KEY ("location key")
);

CREATE TABLE "accommodation_2" (
  "date" TEXT,
  "day of week" TEXT,
  "num days" INTEGER,
  "num nights" INTEGER,
  "num people" INTEGER,
  "party size" TEXT,
  "reservation number" INTEGER,
  "start date" TEXT,
  "reservation time" INTERVAL,
  "time int" TIME,
  "time str" INTEGER,
  PRIMARY KEY ("reservation number"),
  FOREIGN KEY ("date") REFERENCES "accommodation" ("accommodation")
);

CREATE TABLE "train_info_2" (
  "train_info" INTEGER,
  "total fee" TEXT,
  PRIMARY KEY ("train_info")
);
