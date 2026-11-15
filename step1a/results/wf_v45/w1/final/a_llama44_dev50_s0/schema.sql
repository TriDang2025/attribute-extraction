CREATE TABLE "train" (
  "train id" INTEGER,
  "currency" NUMERIC(10, 2),
  "departure station" TEXT,
  "departure time" INTEGER,
  "duration str" INTERVAL,
  "price" NUMERIC(10, 2),
  PRIMARY KEY ("train id")
);

CREATE TABLE "hotel" (
  "date" TEXT,
  "day" TEXT,
  "day of week" TEXT,
  "guest house name" TEXT,
  "hotel name" TEXT,
  "num days" INTEGER,
  "num nights" INTEGER,
  "num people" INTEGER,
  "party size" INTEGER,
  "price range" TEXT,
  "price range str" TEXT,
  "reference number" INTEGER,
  "str" TEXT,
  PRIMARY KEY ("reference number")
);

CREATE TABLE "restaurant" (
  "cuisine" TEXT,
  "date" TEXT,
  "day of week" TEXT,
  "num" INTEGER,
  "phone number" INTEGER,
  "price" TEXT,
  "price range" TEXT,
  "price range str" TEXT,
  "reference number" INTEGER,
  "reservation time" INTERVAL,
  "restaurant name" TEXT,
  "str" TEXT,
  "time int" TIME,
  "time str" INTEGER,
  "venue name" TEXT,
  "hotel id" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("hotel id") REFERENCES "hotel" ("reference number")
);

CREATE TABLE "event" (
  "train id key" INTEGER,
  "day of week str" TEXT,
  "location capitalized" TEXT,
  "time" TIME,
  "time int" TIME,
  "time str" INTEGER,
  "train id" TIME,
  "entity" TEXT,
  "location" TEXT,
  "location part" TEXT,
  "train id (hotel:23)" INTEGER,
  "address" INTEGER,
  "location (restaurant:5)" TEXT,
  "location abbrev" TEXT,
  "location area" TEXT,
  "location str" TEXT,
  PRIMARY KEY ("train id key")
);
