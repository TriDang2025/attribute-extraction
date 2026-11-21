CREATE TABLE "accommodation" (
  "accommodation" INTEGER,
  "num days" INTEGER,
  "entity" TEXT,
  "num people" INTEGER,
  "internet" TEXT,
  "attribute" TEXT,
  PRIMARY KEY ("accommodation")
);

CREATE TABLE "train_info" (
  "booking id key" INTEGER,
  "train id" TIME,
  "location abbr" TEXT,
  "currency" NUMERIC(10, 2),
  "departure time" INTEGER,
  "time" TIME,
  "departure location" TEXT,
  "location type" TEXT,
  "location" TEXT,
  "seating_capacity" INTEGER,
  "travel time" TEXT,
  "total fee" TEXT,
  "day of week" TEXT,
  "booking id" INTEGER,
  "day of week str" TEXT,
  "duration str" INTERVAL,
  "time str" TIME,
  "departure station" TEXT,
  "time int" INTEGER,
  "reference number" INTEGER,
  "price" NUMERIC(10, 2),
  "location str" TEXT,
  PRIMARY KEY ("booking id key")
);

CREATE TABLE "food_establishment" (
  "name id" INTEGER,
  "hotel name" TEXT,
  "guest house name" TEXT,
  "address" INTEGER,
  "cuisine" TEXT,
  "location" TEXT,
  "food type" TEXT,
  "phone number" INTEGER,
  "price range" TEXT,
  "entry fee" TEXT,
  "num" INTEGER,
  "restaurant name" TEXT,
  "location area" TEXT,
  "day of week" TEXT,
  "reservation time" INTERVAL,
  "venue name" TEXT,
  "time str" INTEGER,
  "price" TEXT,
  "time int" TIME,
  PRIMARY KEY ("name id")
);

CREATE TABLE "address" (
  "location str" TEXT,
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
  "location" TEXT,
  "reference number" INTEGER,
  PRIMARY KEY ("postcode"),
  FOREIGN KEY ("reference number") REFERENCES "food_establishment" ("name id")
);

CREATE TABLE "accommodation_2" (
  "reservation number key" INTEGER,
  "date" TEXT,
  "str" TEXT,
  "price range" TEXT,
  "area" TEXT,
  "amenities" TEXT,
  "day of week" TEXT,
  "price" TEXT,
  "start date" TEXT,
  "train id" INTEGER,
  "party size" TEXT,
  "reservation number" INTEGER,
  "num nights" INTEGER,
  "phone number" INTEGER,
  "parking" TEXT,
  "location" TEXT,
  "attraction name" TEXT,
  PRIMARY KEY ("reservation number key")
);
