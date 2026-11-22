CREATE TABLE "accommodation" (
  "reservation number key" INTEGER,
  "price range" TEXT,
  "date" TEXT,
  "reservation number" INTEGER,
  "day of week" TEXT,
  PRIMARY KEY ("reservation number key")
);

CREATE TABLE "train_info" (
  "train id key" INTEGER,
  "time int" INTEGER,
  "departure time" TIME,
  "departure location" TEXT,
  "location abbr" TEXT,
  "departure station" TEXT,
  "currency" NUMERIC(10, 2),
  "departure day" TEXT,
  "train id" TIME,
  "location str" TEXT,
  "duration str" INTERVAL,
  "departure day (train_info:4)" TEXT,
  "location" TEXT,
  "total fee" TEXT,
  PRIMARY KEY ("train id key")
);

CREATE TABLE "food_establishment" (
  "food_establishment" INTEGER,
  "price" TEXT,
  "entry fee" TEXT,
  "time str" INTEGER,
  "reservation time" INTERVAL,
  "entrance fee" NUMERIC(10, 2),
  PRIMARY KEY ("food_establishment")
);

CREATE TABLE "location" (
  "location id" INTEGER,
  "location" TEXT,
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
  "food_establishment id" INTEGER,
  PRIMARY KEY ("location id"),
  FOREIGN KEY ("food_establishment id") REFERENCES "food_establishment" ("food_establishment")
);
